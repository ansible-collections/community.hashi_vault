#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2024, Martin Chmielewski (@M4rt1nCh)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
module: vault_database_connections_list
version_added: 6.2.0
author:
  - Martin Chmielewski (@M4rt1nCh)
short_description: Returns a list of available connections
requirements:
  - C(hvac) (L(Python library,https://hvac.readthedocs.io/en/stable/overview.html))
  - For detailed requirements, see R(the collection requirements page,ansible_collections.community.hashi_vault.docsite.user_guide.requirements).
description:
  - L(List Database Connections,https://hvac.readthedocs.io/en/stable/usage/secrets_engines/database.html#list-connections).
notes:
  - This module always reports C(changed) as False as it is a read operation that doesn't modify data.
  - Use C(changed_when) to control that in cases where the operation is known to not change state.
extends_documentation_fragment:
  - community.hashi_vault.attributes
  - community.hashi_vault.attributes.action_group
  - community.hashi_vault.attributes.check_mode_read_only
  - community.hashi_vault.connection
  - community.hashi_vault.auth
  - community.hashi_vault.engine_mount
"""

EXAMPLES = r"""
- name: List Database Connections with the default mount point
  community.hashi_vault.vault_database_connections_list:
    url: https://vault:8201
    auth_method: userpass
    username: '{{ user }}'
    password: '{{ passwd }}'
  register: result

- name: Display the result of the operation
  ansible.builtin.debug:
    msg: "{{ result }}"

- name: List Database Connections with a custom mount point
  community.hashi_vault.vault_database_connections_list:
    url: https://vault:8201
    auth_method: userpass
    username: '{{ user }}'
    password: '{{ passwd }}'
    engine_mount_point: db1
  register: result

- name: Display the result of the operation
  ansible.builtin.debug:
    msg: "{{ result }}"
"""

RETURN = r"""
data:
  description: The C(data) field of raw result. This can also be accessed via RV(raw.data).
  returned: success
  type: dict
  contains: &data_contains
    keys:
      description: The list of database connections.
      returned: success
      type: list
      elements: str
      sample: &sample_connections ["role1", "role2", "role3"]
  sample:
    keys: *sample_connections
connections:
  description: The list of database connections or en empty list. This can also be accessed via RV(data.keys) or RV(raw.data.keys).
  returned: success
  type: list
  elements: str
  sample: *sample_connections
raw:
  description: The raw result of the operation.
  returned: success
  type: dict
  contains:
    data:
      description: The data field of the API response.
      returned: success
      type: dict
      contains: *data_contains
  sample:
    auth: null
    data:
      keys: *sample_connections
    lease_duration": 0
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
        engine_mount_point=dict(type="str", required=False),
    )

    module = HashiVaultModule(argument_spec=argspec, supports_check_mode=True)

    if not HAS_HVAC:
        module.fail_json(msg=missing_required_lib("hvac"), exception=HVAC_IMPORT_ERROR)

    parameters = {}
    engine_mount_point = module.params.get("engine_mount_point", None)
    if engine_mount_point is not None:
        parameters["mount_point"] = engine_mount_point

    module.connection_options.process_connection_options()
    client_args = module.connection_options.get_hvac_connection_options()
    client = module.helper.get_vault_client(**client_args)

    try:
        module.authenticator.validate()
        module.authenticator.authenticate(client)
    except (NotImplementedError, HashiVaultValueError) as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    try:
        raw = client.secrets.database.list_connections(**parameters)
    except hvac.exceptions.Forbidden as e:
        module.fail_json(
            msg="Forbidden: Permission Denied to path ['%s']." % engine_mount_point
            or "database",
            exception=traceback.format_exc(),
        )
    except hvac.exceptions.InvalidPath as e:
        module.fail_json(
            msg="Invalid or missing path ['%s/config']."
            % (engine_mount_point or "database"),
            exception=traceback.format_exc(),
        )

    data = raw.get("data", {"keys": []})
    connections = data["keys"]
    module.exit_json(
        raw=raw,
        connections=connections,
        data=data,
        changed=False,
    )


def main():
    run_module()


if __name__ == "__main__":
    main()
