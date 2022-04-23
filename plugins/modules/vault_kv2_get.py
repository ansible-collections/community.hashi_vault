#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2022, Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
module: vault_kv2_get
version_added: 2.5.0
author:
  - Brian Scholer (@briantist)
short_description: Get a secret from HashiCorp Vault's KV version 2 secret store
requirements:
  - C(hvac) (L(Python library,https://hvac.readthedocs.io/en/stable/overview.html))
  - For detailed requirements, see R(the collection requirements page,ansible_collections.community.hashi_vault.docsite.user_guide.requirements).
description:
  - Gets a secret from HashiCorp Vault's KV version 2 secret store.
seealso:
  - module: community.hashi_vault.vault_kv1_get
  - module: community.hashi_vault.vault_read
  - ref: community.hashi_vault.vault_read lookup <ansible_collections.community.hashi_vault.vault_read_lookup>
    description: The official documentation for the C(community.hashi_vault.vault_read) lookup plugin.
  - name: KV2 Secrets Engine
    description: Documentation for the Vault KV secrets engine, version 2.
    link: https://www.vaultproject.io/docs/secrets/kv/kv-v2
extends_documentation_fragment:
  - community.hashi_vault.connection
  - community.hashi_vault.auth
  - community.hashi_vault.backend_mount
options:
  backend_mount_point:
    default: secret
  path:
    description:
      - Vault KV path to be read.
      - This is relative to the I(backend_mount_point), so the mount path should not be included.
      - For kv2, do not include C(/data/) or C(/metadata/).
    type: str
    required: True
  version:
    description: Specifies the version to return. If not set the latest version is returned.
    type: int
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
      data:
        Key1: value1
        Key2: value2
      metadata:
        created_time: "2022-04-21T15:56:58.8525402Z"
        custom_metadata": null
        deletion_time": ""
        destroyed": false
        version": 2
    lease_duration: 0
    lease_id: ""
    renewable: false
    request_id: dc829675-9119-e831-ae74-35fc5d33d200
    warnings: null
    wrap_info: null
data:
  description: The C(data) field of raw result. This can also be accessed via C(raw.data).
  returned: success
  type: dict
  sample:
    data:
      Key1: value1
      Key2: value2
    metadata:
      created_time: "2022-04-21T15:56:58.8525402Z"
      custom_metadata": null
      deletion_time": ""
      destroyed": false
      version": 2
secret:
  description: The C(data) field within the C(data) field. Equivalent to C(raw.data.data).
  returned: success
  type: dict
  sample:
    Key1: value1
    Key2: value2
metadata:
  description: The C(metadata) field within the C(data) field. Equivalent to C(raw.data.metadata).
  returned: success
  type: dict
  sample:
    created_time: "2022-04-21T15:56:58.8525402Z"
    custom_metadata": null
    deletion_time": ""
    destroyed": false
    version": 2
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
        backend_mount_point=dict(type='str', default='secret'),
        path=dict(type='str', required=True),
        version=dict(type='int'),
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
    version = module.params.get('version')

    module.connection_options.process_connection_options()
    client_args = module.connection_options.get_hvac_connection_options()
    client = module.helper.get_vault_client(**client_args)

    try:
        module.authenticator.validate()
        module.authenticator.authenticate(client)
    except (NotImplementedError, HashiVaultValueError) as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    try:
        raw = client.secrets.kv.v2.read_secret_version(path=path, version=version, mount_point=backend_mount_point)
    except hvac.exceptions.Forbidden as e:
        module.fail_json(msg="Forbidden: Permission Denied to path ['%s']." % path, exception=traceback.format_exc())
    except hvac.exceptions.InvalidPath as e:
        module.fail_json(
            msg="Invalid or missing path ['%s'] with secret version '%s'. Check the path or secret version." % (path, version or 'latest'),
            exception=traceback.format_exc()
        )

    data = raw['data']
    metadata = data['metadata']
    secret = data['data']
    module.exit_json(raw=raw, data=data, secret=secret, metadata=metadata)


def main():
    run_module()


if __name__ == '__main__':
    main()