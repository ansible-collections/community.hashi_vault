#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2023, Devon Mar (@devon-mar)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
module: vault_kv2_write
version_added: 4.2.0
author:
  - Devon Mar (@devon-mar)
short_description: Perform a write/patch operation against a KVv2 secret in HashiCorp Vault
description:
  - Perform a write/patch operation against a KVv2 secret in HashiCorp Vault.
requirements:
  - C(hvac) (L(Python library,https://hvac.readthedocs.io/en/stable/overview.html))
  - For detailed requirements, see R(the collection requirements page,ansible_collections.community.hashi_vault.docsite.user_guide.requirements).
extends_documentation_fragment:
  - community.hashi_vault.attributes
  - community.hashi_vault.attributes.action_group
  - community.hashi_vault.connection
  - community.hashi_vault.auth
  - community.hashi_vault.engine_mount
attributes:
  check_mode:
    support: full
options:
  engine_mount_point:
    type: str
    default: secret
  path:
    type: str
    required: true
    description:
      - Vault KVv2 path to be written to.
      - This is relative to the I(engine_mount_point), so the mount path should not be included.
  data:
    type: dict
    required: true
    description:
      - KVv2 secret data to write/patch.
  patch:
    type: bool
    default: false
    description:
      - Update an existing KVv2 secret with C(data) instead of overwriting.
      - The secret must already exist.
      - I(cas) must be C(false).
  cas:
    type: int
    description:
      - Perform a check-and-set operation.
      - C(patch) must be C(false).
"""

EXAMPLES = r"""
- name: Write/create a secret
  community.hashi_vault.vault_kv2_write:
    url: https://vault:8201
    path: hello
    data:
      foo: bar

- name: Patch an existing secret
  community.hashi_vault.vault_kv2_write:
    url: https://vault:8201
    path: hello
    data:
      my: new key

- name: Write with check and set
  community.hashi_vault.vault_kv2_write:
    url: https://vault:8201
    path: caspath
    cas: 0
    data:
      foo: bar
"""

RETURN = r"""
raw:
  type: dict
  description: The raw Vault response.
  returned: changed
  sample:
    auth:
    data:
      created_time: "2023-02-21T19:51:50.801757862Z"
      custom_metadata:
      deletion_time: ""
      destroyed: false
      version: 1
    lease_duration: 0
    lease_id: ""
    renewable: false
    request_id: 52eb1aa7-5a38-9a02-9246-efc5bf9581ec
    warnings: null
    wrap_info: null
"""

import traceback

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import missing_required_lib
from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import \
    HashiVaultValueError
from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_module import \
    HashiVaultModule

try:
    import hvac
except ImportError:
    HAS_HVAC = False
    HVAC_IMPORT_ERROR = traceback.format_exc()
else:
    HVAC_IMPORT_ERROR = None
    HAS_HVAC = True


def run_module():
    argspec = HashiVaultModule.generate_argspec(
        engine_mount_point=dict(type="str", default="secret"),
        path=dict(type="str", required=True),
        data=dict(type="dict", required=True),
        cas=dict(type="int"),
        patch=dict(type="bool", default=False),
    )

    module = HashiVaultModule(
        argument_spec=argspec,
        supports_check_mode=True,
    )

    if not HAS_HVAC:
        module.fail_json(
            msg=missing_required_lib("hvac"),
            exception=HVAC_IMPORT_ERROR,
        )

    mount_point = module.params.get("engine_mount_point")
    path = module.params.get("path")
    cas = module.params.get("cas")
    data = module.params.get("data")
    patch = module.params.get("patch")

    module.connection_options.process_connection_options()
    client_args = module.connection_options.get_hvac_connection_options()
    client = module.helper.get_vault_client(**client_args)

    if cas and patch is True:
        module.fail_json(msg="Cannot use cas when patch is true.")

    try:
        module.authenticator.validate()
        module.authenticator.authenticate(client)
    except (NotImplementedError, HashiVaultValueError) as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    try:
        response = client.secrets.kv.v2.read_secret_version(
            path=path, mount_point=mount_point
        )
        if "data" not in response or "data" not in response["data"]:
            module.fail_json(msg="Vault response did not contain data: %s" % response)
        current_data = response["data"]["data"]
    except hvac.exceptions.InvalidPath:
        if patch is True:
            module.fail_json(
                msg="Path '%s' has not been written to previously. Patch only works on an existing secret."
                % path,
                exception=traceback.format_exc(),
            )
        current_data = {}
    except hvac.exceptions.Forbidden:
        module.fail_json(
            msg="Permission denied reading %s" % path,
            exception=traceback.format_exc(),
        )
    except hvac.exceptions.VaultError:
        module.fail_json(
            msg="VaultError reading %s" % path,
            exception=traceback.format_exc(),
        )

    if patch is True:
        changed = any(current_data.get(k) != v for k, v in data.items())
    else:
        changed = current_data != data

    if changed is True and module.check_mode is False:
        args = {
            "path": path,
            "secret": data,
            "mount_point": mount_point,
        }
        if cas:
            args["cas"] = cas

        try:
            if patch is True:
                raw = client.secrets.kv.v2.patch(**args)
            else:
                raw = client.secrets.kv.v2.create_or_update_secret(**args)
        except hvac.exceptions.Forbidden:
            module.fail_json(
                msg="Permission denied writing to '%s'" % path,
                exception=traceback.format_exc(),
            )

        module.exit_json(changed=True, raw=raw)

    module.exit_json(changed=changed)


def main():
    run_module()


if __name__ == "__main__":
    main()
