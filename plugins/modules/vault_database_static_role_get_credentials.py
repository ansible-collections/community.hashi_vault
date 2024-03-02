#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2024, Martin Chmielewski (@M4rt1nCh)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
module: vault_database_static_role_get_credentials
version_added: 6.2.0
author:
  - Martin Chmielewski (@M4rt1nCh)
short_description: Returns the current credentials based on the named static role
requirements:
  - C(hvac) (L(Python library,https://hvac.readthedocs.io/en/stable/overview.html))
  - For detailed requirements, see R(the collection requirements page,ansible_collections.community.hashi_vault.docsite.user_guide.requirements).
description:
  - Returns the current credentials based on the named static role
notes:
  - C(vault_database_static_role_get_credentials) reads a static role
  - https://hvac.readthedocs.io/en/stable/usage/secrets_engines/database.html#get-static-credentials
  - The I(data) option is not treated as secret and may be logged. Use the C(no_log) keyword if I(data) contains sensitive values.
  - This module always reports C(changed) as False as it is a read operation that doesn't modify data.
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
  role_name:
    description: The role name from which the credentials should be retrieved.
    type: str
    required: True
'''

EXAMPLES = r"""
- name: Returns the current credentials based on the named static role
  community.hashi_vault.vault_database_static_role_read:
    path: database
    role_name: SomeRole
  register: response

- name: Display the result of the operation
  ansible.builtin.debug:
    msg: "{{ result }}"
"""

RETURN = r"""
data:
  description: The C(data) field of raw result. This can also be accessed via C(raw.data).
  returned: success
  type: dict
  sample:
    last_vault_rotation": "2024-01-01T09:00:00+01:00"
    password": "Th3_$3cr3t_P@ss!"
    rotation_period": 86400
    ttl": 123456
    username: "SomeUser"
raw:
  description: The raw result of the operation.
  returned: success
  type: dict
  sample:
    auth: null,
    data:
      last_vault_rotation": "2024-01-01T09:00:00+01:00"
      password": "Th3_$3cr3t_P@ss!"
      rotation_period": 86400
      ttl": 123456
      username: "SomeUser"
    lease_duration: 0
    lease_id: ""
    renewable: false
    request_id: "123456"
    warnings: null,
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
        role_name=dict(type='str', required=True),
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
    role_name = module.params.get('role_name')

    module.connection_options.process_connection_options()
    client_args = module.connection_options.get_hvac_connection_options()
    client = module.helper.get_vault_client(**client_args)

    try:
        module.authenticator.validate()
        module.authenticator.authenticate(client)
    except (NotImplementedError, HashiVaultValueError) as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    try:
        raw = client.secrets.database.get_static_credentials(
            name=role_name,
            mount_point=path,
        )
    except hvac.exceptions.Forbidden as e:
        module.fail_json(msg="Forbidden: Permission Denied to path ['%s']." % path, exception=traceback.format_exc())
    except hvac.exceptions.InvalidPath as e:
        module.fail_json(
            msg="Invalid or missing path ['%s']. Check the path." % (path),
            exception=traceback.format_exc()
        )

    data = raw['data']

    module.exit_json(
        data=data,
        raw=raw,
        changed=False
    )


def main():
    run_module()


if __name__ == '__main__':
    main()