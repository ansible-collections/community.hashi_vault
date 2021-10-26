#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2021, Devon Mar (@devon-mar)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
module: vault_kv2
version_added: 1.4.0
author:
  - Devon Mar (@devon-mar)
short_description: Performs various HashiCorp Vault KV v2 write operations on secrets.
description:
  - Performs various HashiCorp Vault KV v2 operations on secrets including delete, destroy, undelete, patch, and write.
extends_documentation_fragment:
  - community.hashi_vault.connection
  - community.hashi_vault.auth
options:
  path:
    description: Vault path to write to excluding the secret store.
    type: str
    required: true
  data:
    type: dict
    description:
      - Data to write.
      - Used when I(state=present).
  cas:
    type: int
    description:
      - Used to perform a check-and-set operation.
      - Used when I(state=present) and I(patch=false).
  cas_required:
    type: bool
    description: Configures C(cas_required) on the individual secret. Used when I(state=present).
  max_versions:
    type: int
    description: The number of versions to keep per key. Used when I(state=present).
  delete_version_after:
    type: str
    description:
      - Specifies the length of time before a version is deleted. Accepts a Go duration format string.
      - Used when I(state=present).
  patch:
    type: bool
    default: false
    description: When I(state=present) combines I(data) with existing data instead of replacing them.
  state:
    type: str
    choices:
      - present
      - deleted
      - destroyed
      - absent
      - undeleted
    default: present
    description:
      - C(present) ensures the secret is present or that the specific key/value pairs are present when I(patch=true).
      - C(deleted) ensures the versions in I(versions) are soft deleted.
      - C(destroyed) ensures the versions in I(versions) are permanently destroyed.
      - C(undeleted) ensures the versions in I(versions) are not soft deleted.
      - C(absent) ensures all metadata and versions for the secret are absent.
  kv2_mount:
    type: str
    default: secret
    description: Mount point of the KV v2 secret store.
  versions:
    type: list
    elements: int
    default: []
    description:
      - Versions of the secret to delete. If empty, the latest version will be used.
      - Used with I(state=destroyed), I(state=deleted) and I(state=undeleted).
"""

EXAMPLES = """
- name: vault kv put secret/cred password=passw0rd
  community.hashi_vault.vault_kv2:
    path: secret/cred
    data:
      password: passw0rd
    state: present

- name: vault kv patch secret/cred username=user
  community.hashi_vault.vault_kv2:
    path: secret/cred
    data:
      username: user
    patch: true
    state: present

- name: vault kv delete secret/cred
  community.hashi_vault.vault_kv2:
    path: secret/cred
    state: deleted

- name: vault kv delete -versions=3 secret/cred
  community.hashi_vault.vault_kv2:
    path: secret/cred
    versions:
      - 3
    state: deleted

- name: vault kv destroy -versions=3 secret/cred
  community.hashi_vault.vault_kv2:
    path: secret/cred
    versions:
      - 3
    state: destroyed

- name: vault kv metadata delete secret/cred
  community.hashi_vault.vault_kv2:
    path: secret/cred
    state: absent
"""

RETURN = """
data:
  description: The response from Vault.
  returned: when state=present
  type: dict
"""
import traceback

from ansible.module_utils._text import to_native

from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_module import HashiVaultModule
from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import HashiVaultValueError


HAS_HVAC = False
try:
    import hvac
    HAS_HVAC = True
except ImportError as e:
    HVAC_IMPORT_ERROR = traceback.format_exc()
    HAS_HVAC = False


def update_metadata(client, module, path, mount_point):
    """
    :rtype: bool
    :returns: Whether or not changes were made.
    """
    changed = False

    params = {
        "cas_required": module.params.get("cas_required"),
        "max_versions": module.params.get("max_versions"),
        "delete_version_after": module.params.get("delete_version_after")
    }

    if all(p is None for p in params.values()):
        return False

    args = {"path": path}
    if mount_point is not None:
        args["mount_point"] = mount_point

    try:
        metadata = client.secrets.kv.v2.read_secret_metadata(path, mount_point=mount_point)
    except hvac.exceptions.InvalidPath:
        return True

    for k, v in params.items():
        if v is not None and metadata["data"][k] != v:
            changed = True
            args[k] = v

    if changed and not module.check_mode:
        client.secrets.kv.v2.update_metadata(**args)
    return changed


def update_data(client, module, path, mount_point):
    result = {"changed": False}

    data = module.params.get("data")
    patch = module.params.get("patch")
    cas = module.params.get("cas")

    if data is None:
        return result

    # Read the latest version
    try:
        response = client.secrets.kv.v2.read_secret_version(path=path, mount_point=mount_point)
        if "data" not in response:
            module.fail_json(msg="hvac response did not contain data: %s" % response)
        current_secret = response["data"]["data"]
    except hvac.exceptions.InvalidPath:
        current_secret = {}
    except hvac.exceptions.Forbidden:
        module.fail_json(msg="Permission denied when writing to %s" % path, exception=traceback.format_exc())
    except hvac.exceptions.VaultError:
        module.fail_json(msg="VaultError while reading %s" % path, exception=traceback.format_exc())

    # TODO add diff
    if patch and any(i not in current_secret.items() for i in data.items()):
        result["changed"] = True
    elif not patch and (len(current_secret) != len(data) or any(i not in current_secret.items() for i in data.items())):
        result["changed"] = True

    if result["changed"] and not module.check_mode:
        args = {
            "path": path,
            "secret": data,
            "mount_point": mount_point
        }
        if cas and not patch:
            args["cas"] = cas

        try:
            if patch:
                response = client.secrets.kv.v2.patch(**args)
            else:
                response = client.secrets.kv.v2.create_or_update_secret(**args)
        except hvac.exceptions.InvalidPath as e:
            if patch:
                module.fail_json(
                    msg="Path %s has not been written to previously. Patch only works on existing data." % path,
                    exception=traceback.format_exc()
                )
            else:
                raise e

        if response is None:
            module.fail_json(msg="hvac response was none")
        elif "data" not in response:
            module.fail_json(msg="hvac response did not contain data")
        result["data"] = response

    return result


def state_present(client, module, path, mount_point):
    result = update_data(client, module, path, mount_point)

    if update_metadata(client, module, path, mount_point):
        result["changed"] = True

    module.exit_json(**result)


def state_absent(client, module, path, mount_point):
    try:
        client.secrets.kv.v2.read_secret_metadata(path, mount_point=mount_point)
    except hvac.exceptions.InvalidPath:
        module.exit_json(changed=False)

    if not module.check_mode:
        client.secrets.kv.v2.delete_metadata_and_all_versions(path, mount_point=mount_point)
    module.exit_json(changed=True)


def state_deleted(client, module, path, mount_point):
    versions = module.params.get("versions")

    # We handle latest differently since it uses a different endpoint
    # and therefore uses different permissions.
    if len(versions) == 0:
        metadata = client.secrets.kv.v2.read_secret_metadata(path, mount_point=mount_point)
        latest_version = int(metadata["data"]["current_version"])
        try:
            client.secrets.kv.v2.read_secret_version(
                path,
                version=latest_version,
                mount_point=mount_point
            )
        except hvac.exceptions.InvalidPath:
            # The secret has already been soft-deleted.
            module.exit_json(changed=False)

        if not module.check_mode:
            client.secrets.kv.v2.delete_latest_version_of_secret(path, mount_point=mount_point)
        module.exit_json(changed=True)

    to_delete = []
    for v in versions:
        try:
            client.secrets.kv.v2.read_secret_version(
                path,
                version=v,
                mount_point=mount_point
            )
            to_delete.append(v)
        except hvac.exceptions.InvalidPath:
            # The secret has already been soft-deleted.
            pass

    if len(to_delete) > 0:
        if not module.check_mode:
            client.secrets.kv.v2.delete_secret_versions(path, to_delete, mount_point=mount_point)
        module.exit_json(changed=True)
    module.exit_json(changed=False)


def state_destroyed(client, module, path, mount_point):
    versions = module.params.get("versions")

    metadata = client.secrets.kv.v2.read_secret_metadata(path, mount_point=mount_point)

    if len(versions) == 0:
        versions.append(int(metadata["data"]["current_version"]))

    to_delete = []

    for v in versions:
        if str(v) not in metadata["data"]["versions"]:
            module.fail_json(msg="Version %d is not valid for %s" % (v, path))
        to_delete.append(v)

    if len(to_delete) > 0:
        if not module.check_mode:
            client.secrets.kv.v2.destroy_secret_versions(path, to_delete, mount_point=mount_point)
        module.exit_json(changed=True)
    module.exit_json(changed=False)


def state_undeleted(client, module, path, mount_point):
    versions = module.params.get("versions")

    if len(versions) == 0:
        metadata = client.secrets.kv.v2.read_secret_metadata(path, mount_point=mount_point)
        versions.append(int(metadata["data"]["current_version"]))

    to_undelete = []
    for v in versions:
        try:
            client.secrets.kv.v2.read_secret_version(
                path,
                version=v,
                mount_point=mount_point
            )
        except hvac.exceptions.InvalidPath:
            # The secret has been soft-deleted.
            to_undelete.append(v)
            pass

    if len(to_undelete) > 0:
        if not module.check_mode:
            client.secrets.kv.v2.undelete_secret_versions(path, to_undelete, mount_point=mount_point)
        module.exit_json(changed=True)
    module.exit_json(changed=False)


def run_module():
    argspec = HashiVaultModule.generate_argspec(
        path=dict(type="str", required=True),
        data=dict(type="dict"),
        kv2_mount=dict(type="str", default="secret"),
        patch=dict(type="bool", default=False),
        state=dict(type="str", default="present", choices=["present", "deleted", "destroyed", "absent", "undeleted"]),
        versions=dict(type="list", elements="int", default=[]),
        cas=dict(type="int"),
        cas_required=dict(type="bool"),
        max_versions=dict(type="int"),
        delete_version_after=dict(type="str")
    )

    module = HashiVaultModule(
        argument_spec=argspec,
        required_if=[("state", "present", ("data",))],
        supports_check_mode=True
    )

    if not HAS_HVAC:
        module.fail_json(msg="hvac is not installed", exception=HVAC_IMPORT_ERROR)

    module.connection_options.process_connection_options()
    client_args = module.connection_options.get_hvac_connection_options()
    client = module.helper.get_vault_client(**client_args)

    try:
        module.authenticator.validate()
        module.authenticator.authenticate(client)
    except (NotImplementedError, HashiVaultValueError) as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    path = module.params.get("path")
    mount_point = module.params.get("kv2_mount")
    state = module.params.get("state")

    try:
        if state == "present":
            state_present(client, module, path, mount_point)
        elif state == "absent":
            state_absent(client, module, path, mount_point)
        elif state == "deleted":
            state_deleted(client, module, path, mount_point)
        elif state == "destroyed":
            state_destroyed(client, module, path, mount_point)
        elif state == "undeleted":
            state_undeleted(client, module, path, mount_point)
    except hvac.exceptions.InvalidPath:
        module.fail_json(msg="Invalid path %s" % path, exception=traceback.format_exc())
    except hvac.exceptions.Forbidden:
        module.fail_json(msg="Permission denied when writing to %s" % path, exception=traceback.format_exc())
    except hvac.exceptions.VaultError:
        module.fail_json(msg="VaultError on %s" % path, exception=traceback.format_exc())


def main():
    run_module()


if __name__ == "__main__":
    main()
