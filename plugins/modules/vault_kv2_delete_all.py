#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2024, Robin Kloppe
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
module: vault_kv2_delete_all
version_added: 3.4.0
author:
  - Robin Kloppe
short_description: Delete a complete secret from HashiCorp Vault's KV version 2 secret store
requirements:
  - C(hvac) (L(Python library,https://hvac.readthedocs.io/en/stable/overview.html))
  - For detailed requirements, see R(the collection requirements page,ansible_collections.community.hashi_vault.docsite.user_guide.requirements).
description:
  - Delete a complete secret from HashiCorp Vault's KV version 2 secret store.
notes:
  - This module always reports C(changed) status because it cannot guarantee idempotence.
  - Use C(changed_when) to control that in cases where the operation is known to not change state.
attributes:
  check_mode:
    support: partial
    details:
      - In check mode, the module returns C(changed) status without contacting Vault.
      - Consider using M(community.hashi_vault.vault_kv2_get) to verify the existence of the secret first.
seealso:
  - module: community.hashi_vault.vault_kv2_get
  - module: community.hashi_vault.vault_kv2_write
  - module: community:hashi_vault_vault_kv2_delete
  - name: KV2 Secrets Engine
    description: Documentation for the Vault KV secrets engine, version 2.
    link: https://www.vaultproject.io/docs/secrets/kv/kv-v2
extends_documentation_fragment:
  - community.hashi_vault.attributes
  - community.hashi_vault.attributes.action_group
  - community.hashi_vault.connection
  - community.hashi_vault.auth
  - community.hashi_vault.engine_mount
options:
  engine_mount_point:
    default: secret
  path:
    description:
      - Vault KV path to be deleted.
      - This is relative to the I(engine_mount_point), so the mount path should not be included.
      - For kv2, do not include C(/data/) or C(/metadata/).
    type: str
    required: True
'''

EXAMPLES = """
- name: Delete everything of the secret/mysecret secret.
  community.hashi_vault.vault_kv2_delete_all:
    url: https://vault:8201
    path: secret/mysecret
    auth_method: userpass
    username: user
    password: '{{ passwd }}'
  register: result
"""

RETURN = """
data:
  description:
    - The raw result of the delete against the given path.
    - This is usually empty, but may contain warnings or other information.
  returned: success
  type: dict
"""

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
    HVAC_IMPORT_ERROR = None
    HAS_HVAC = True


def run_module():

    argspec = HashiVaultModule.generate_argspec(
        engine_mount_point=dict(type='str', default='secret'),
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

    engine_mount_point = module.params.get('engine_mount_point')
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
        # Vault has two separate methods, one for delete latest version,
        # and delete specific versions.
        if module.check_mode:
            response = {}
        else:
            response = client.secrets.kv.v2.delete_metadata_and_all_versions(
                path=path, mount_point=engine_mount_point)

    except hvac.exceptions.Forbidden as e:
        module.fail_json(msg="Forbidden: Permission Denied to path ['%s']." % path, exception=traceback.format_exc())

    # https://github.com/hvac/hvac/issues/797
    # HVAC returns a raw response object when the body is not JSON.
    # That includes 204 responses, which are successful with no body.
    # So we will try to detect that and a act accordingly.
    # A better way may be to implement our own adapter for this
    # collection, but it's a little premature to do that.
    if hasattr(response, 'json') and callable(response.json):
        if response.status_code == 204:
            output = {}
        else:
            module.warn(
                'Vault returned status code %i and an unparsable body.' % response.status_code)
            output = response.content
    else:
        output = response

    module.exit_json(changed=True, data=output)


def main():
    run_module()


if __name__ == '__main__':
    main()
