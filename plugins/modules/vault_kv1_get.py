#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2022, Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
module: vault_kv1_get
version_added: 2.5.0
author:
  - Brian Scholer (@briantist)
short_description: Get a secret from HashiCorp Vault's KV version 1 secret store
requirements:
  - C(hvac) (L(Python library,https://hvac.readthedocs.io/en/stable/overview.html))
  - For detailed requirements, see R(the collection requirements page,ansible_collections.community.hashi_vault.docsite.user_guide.requirements).
description:
  - Gets a secret from HashiCorp Vault's KV version 1 secret store.
seealso:
  - ref: community.hashi_vault.vault_read lookup <ansible_collections.community.hashi_vault.vault_read_lookup>
    description: The official documentation for the C(community.hashi_vault.vault_read) lookup plugin.
  - module: community.hashi_vault.read
  - name: KV Secrets Engine
    link: https://www.vaultproject.io/docs/secrets/kv
extends_documentation_fragment:
  - community.hashi_vault.connection
  - community.hashi_vault.auth
  - community.hashi_vault.backend_mount
options:
  backend_mount_point:
    default: kv
  path:
    description:
      - Vault KV path to be read.
      - This is relative to the I(backend_mount_point), so the mount path should not be included.
    type: str
    required: True
'''

EXAMPLES = """
- name: Read a kv2 secret from Vault via the remote host with userpass auth
  community.hashi_vault.vault_read:
    url: https://vault:8201
    path: secret/data/hello
    auth_method: userpass
    username: user
    password: '{{ passwd }}'
  register: secret

- name: Display the secret data
  ansible.builtin.debug:
    msg: "{{ secret.data.data.data }}"

- name: Retrieve an approle role ID from Vault via the remote host
  community.hashi_vault.vault_read:
    url: https://vault:8201
    path: auth/approle/role/role-name/role-id
  register: approle_id

- name: Display the role ID
  ansible.builtin.debug:
    msg: "{{ approle_id.data.data.role_id }}"
"""

RETURN = r'''
raw:
  description: The raw result of the read against the given path.
  returned: success
  type: dict
  sample:
    auth: null
    data:
      Key1: value1
      Key2: value2
    lease_duration: 2764800
    lease_id: ""
    renewable: false
    request_id: e99f145f-f02a-7073-1229-e3f191057a70
    warnings: null
    wrap_info: null
data:
  description: The C(data) field of raw result. This can also be accessed via C(raw.data).
  returned: success
  type: dict
  sample:
    Key1: value1
    Key2: value2
secret:
  description: The C(data) field of the raw result. This is identical to C(data) in the return values.
  returned: success
  type: dict
  sample:
    Key1: value1
    Key2: value2
metadata:
  description: This is a synthetic result. It is the same as C(raw) with C(data) removed.
  returned: success
  type: dict
  sample:
    auth: null
    lease_duration: 2764800
    lease_id: ""
    renewable: false
    request_id: e99f145f-f02a-7073-1229-e3f191057a70
    warnings: null
    wrap_info: null
'''

import traceback

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import missing_required_lib

from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_module import HashiVaultModule
from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import HashiVaultValueError

try:
    import hvac
except ImportError:
    HAS_HVAC = False
    HVAC_IMPORT_ERROR = traceback.format_exc()
else:
    HAS_HVAC = True


def run_module():
    argspec = HashiVaultModule.generate_argspec(
        backend_mount_point=dict(type='str', default='kv'),
        path=dict(type='str', required=True),
    )

    module = HashiVaultModule(
        argument_spec=argspec,
        supports_check_mode=True
    )

    if not HAS_HVAC:
        module.fail_json(
            msg=missing_required_lib('hvac'),
            exception=HVAC_IMPORT_ERROR
        )

    backend_mount_point = module.params.get('backend_mount_point')
    path = module.params.get('path')

    module.connection_options.process_connection_options()
    client_args = module.connection_options.get_hvac_connection_options()
    client = module.helper.get_vault_client(**client_args)

    try:
        module.authenticator.validate()
        module.authenticator.authenticate(client)
    except (NotImplementedError, HashiVaultValueError) as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    try:
        raw = client.secrets.kv.v1.read_secret(path=path, mount_point=backend_mount_point)
    except hvac.exceptions.Forbidden as e:
        module.fail_json(msg="Forbidden: Permission Denied to path '%s'." % path, exception=traceback.format_exc())
    except hvac.exceptions.InvalidPath as e:
        if 'Invalid path for a versioned K/V secrets engine' in to_native(e):
            msg = "Invalid path for a versioned K/V secrets engine ['%s']. If this is a KV version 2 path, use community.hashi_vault.vault_kv2_get."
        else:
            msg="Invalid Path ['%s']."

        module.fail_json(msg=msg % (path,), exception=traceback.format_exc())

    if raw is None:
        module.fail_json(msg="The path '%s' doesn't seem to exist." % path)

    metadata = raw.copy()
    data = metadata.pop('data')
    module.exit_json(raw=raw, data=data, secret=data, metadata=metadata)


def main():
    run_module()


if __name__ == '__main__':
    main()
