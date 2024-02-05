#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2024, Martin Chmielewski (@M4rt1nCh)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
module: vault_database_role_create
version_added: 2.6.0
author:
  - Martin Chmielewski (@M4rt1nCh)
short_description: Creates or updates a (dynamic) role definition
requirements:
  - C(hvac) (L(Python library,https://hvac.readthedocs.io/en/stable/overview.html))
  - For detailed requirements, see R(the collection requirements page,ansible_collections.community.hashi_vault.docsite.user_guide.requirements).
description:
  - Creates or updates a (dynamic) role definition
notes:
  - C(vault_database_role_create) triggers the creation of a static role
  - https://hvac.readthedocs.io/en/stable/usage/secrets_engines/database.html#create-static-role
  - The I(data) option is not treated as secret and may be logged. Use the C(no_log) keyword if I(data) contains sensitive values.
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
    description: The connection name under which the role should be created.
    type: str
    required: True
  role_name:
    description: The name of the role that should be created.
    type: str
    required: True
  creation_statements:
    description: Specifies the database statements executed to create and configure a user.
    type: list
    required: True
    elements: str
  revocation_statements:
    description: Specifies the database statements to be executed to revoke a user.
    type: list
    required: False
    elements: str
  rollback_statements:
    description: Specifies the database statements to be executed to rollback a create operation in the event of an error.
    type: list
    required: False
    elements: str
  renew_statements:
    description: Specifies the database statements to be executed to renew a user
    type: list
    required: False
    elements: str
  default_ttl:
    description: Default TTL for the role.
    type: int
    required: False
    default: 3600
  max_ttl:
    description: Max TTL for the role.
    type: int
    required: False
    default: 86400
'''

EXAMPLES = r"""
- name: Generate creation statement
  ansible.builtin.set_fact:
    creation_statements = [
        "CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}';",
        "GRANT SELECT ON ALL TABLES IN SCHEMA public TO \"{{name}}\";"
    ]

- name: Create / update Role
  community.hashi_vault.vault_database_role_create:
    path: database
    connection_name: SomeConnection
    role_name: SomeRole
    db_username: '{{ db_username}}'
    creation_statements: '{{ creation_statements }}'
  register: response

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
    status: "success"
raw:
  description: The raw result of the operation.
  returned: success
  type: dict
  sample:
    auth: null
    data: null
    lease_duration: 0
    lease_id: ""
    renewable: false
    request_id: "123456"
    warnings: null
    wrap_info: null
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
        role_name=dict(type='str', required=True),
        creation_statements=dict(type='list', required=True, elements='str'),
        revocation_statements=dict(type='list', required=False, elements='str'),
        rollback_statements=dict(type='list', required=False, elements='str'),
        renew_statements=dict(type='list', required=False, elements='str'),
        default_ttl=dict(type='int', required=False, default=3600),
        max_ttl=dict(type='int', required=False, default=86400),
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
    role_name = module.params.get('role_name')
    creation_statements = module.params.get('creation_statements')
    revocation_statements = module.params.get('revocation_statements')
    rollback_statements = module.params.get('rollback_statements')
    renew_statements = module.params.get('renew_statements')
    default_ttl = module.params.get('default_ttl')
    max_ttl = module.params.get('max_ttl')

    module.connection_options.process_connection_options()
    client_args = module.connection_options.get_hvac_connection_options()
    client = module.helper.get_vault_client(**client_args)

    try:
        module.authenticator.validate()
        module.authenticator.authenticate(client)
    except (NotImplementedError, HashiVaultValueError) as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    try:
        raw = client.secrets.database.create_role(
            name=role_name,
            db_name=connection_name,
            mount_point=path,
            creation_statements=creation_statements,
            revocation_statements=revocation_statements,
            rollback_statements=rollback_statements,
            renew_statements=renew_statements,
            default_ttl=default_ttl,
            max_ttl=max_ttl,
        )
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
