#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2024, Martin Chmielewski (@M4rt1nCh)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
module: vault_database_connection_reset
version_added: 6.2.0
author:
  - Martin Chmielewski (@M4rt1nCh)
short_description: Resets a Database Connection (identified by its connection_name) in a given path
requirements:
  - C(hvac) (L(Python library,https://hvac.readthedocs.io/en/stable/overview.html))
  - For detailed requirements, see R(the collection requirements page,ansible_collections.community.hashi_vault.docsite.user_guide.requirements).
description:
  - Reads
notes:
  - C(vault_database_connection_reset) resets a database connection from Hashicorp as described in
  - https://hvac.readthedocs.io/en/stable/usage/secrets_engines/database.html#reset-connection
  - This module always reports C(changed) status because it cannot guarantee idempotence.
  - Use C(changed_when) to control that in cases where the operation is known to not change state.
attributes:
  check_mode:
    support: partial
    details:
      - In check mode, an empty response will be returned and the write will not be performed.
extends_documentation_fragment:
  - community.hashi_vault.attributes
  - community.hashi_vault.attributes.action_group
  - community.hashi_vault.connection
  - community.hashi_vault.auth
options:
  path:
    description: Vault path of a database secrets engine.
    type: str
    required: True
  connection_name:
    description: The connection name to be resetted.
    type: str
    required: True
'''

EXAMPLES = r"""
- name: Reset a Database Connection
  community.hashi_vault.vault_database_connection_reset:
    url: https://vault:8201
    path: database
    connection_name: SomeName
    auth_method: userpass
    username: user
    password: '{{ passwd }}'
  register: result

- name: Display the result of the operation
  ansible.builtin.debug:
    msg: "{{ result }}"
"""

RETURN = r"""
data:
  description: The result of the operation.
  returned: success
  type: dict
  sample:
    data:
      ok: true
      status: "success"
      status_code: 204
"""

import traceback

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import missing_required_lib

from ..module_utils._hashi_vault_module import HashiVaultModule
from ..module_utils._hashi_vault_common import HashiVaultValueError

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
        path=dict(type='str', required=True),
        connection_name=dict(type='str', required=True),
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

    path = module.params.get('path')
    connection_name = module.params.get('connection_name')

    module.connection_options.process_connection_options()
    client_args = module.connection_options.get_hvac_connection_options()
    client = module.helper.get_vault_client(**client_args)

    try:
        module.authenticator.validate()
        module.authenticator.authenticate(client)
    except (NotImplementedError, HashiVaultValueError) as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    try:
        raw = client.secrets.database.reset_connection(name=connection_name, mount_point=path)
    except hvac.exceptions.Forbidden as e:
        module.fail_json(msg="Forbidden: Permission Denied to path ['%s']." % path, exception=traceback.format_exc())
    except hvac.exceptions.InvalidPath as e:
        module.fail_json(
            msg="Invalid or missing path ['%s']. Check the path." % (path),
            exception=traceback.format_exc()
        )

    if raw.status_code not in [200, 204]:
        module.fail_json(
            status='failure',
            msg="Failed to create connection. Status code: %s" % raw.status_code,
        )
    module.exit_json(
        data={
            'status': 'success',
            'status_code': raw.status_code,
            'ok': raw.ok,
        },
        changed=True
    )


def main():
    run_module()


if __name__ == '__main__':
    main()