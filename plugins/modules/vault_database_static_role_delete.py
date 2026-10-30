#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Saran Kumar (@sarankumar1325)
# Based on vault_database_role_delete by Martin Chmielewski (@M4rt1nCh)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
module: vault_database_static_role_delete
version_added: 7.2.0
author:
  - Saran Kumar (@sarankumar1325)
short_description: Delete a static role definition
requirements:
  - C(hvac) (L(Python library,https://hvac.readthedocs.io/en/stable/overview.html))
  - For detailed requirements, see R(the collection requirements page,ansible_collections.community.hashi_vault.docsite.user_guide.requirements).
description:
  - L(Delete a static role definition,https://hvac.readthedocs.io/en/stable/usage/secrets_engines/database.html#delete-a-static-role).
notes:
  - Only deletes static roles. Use M(community.hashi_vault.vault_database_role_delete) to delete dynamic roles.
  - This module always reports C(changed) status because it cannot guarantee idempotence.
  - Use C(changed_when) to control that in cases where the operation is known to not change state.
attributes:
  check_mode:
    support: partial
    details:
      - In check mode, a sample response will be returned, but the deletion will not be performed in Hashicorp Vault.
extends_documentation_fragment:
  - community.hashi_vault.attributes
  - community.hashi_vault.attributes.action_group
  - community.hashi_vault.connection
  - community.hashi_vault.auth
  - community.hashi_vault.engine_mount
options:
  role_name:
    description: The name of the static role to delete.
    type: str
    required: True
"""

EXAMPLES = r"""
- name: Delete a static role with the default mount point
  community.hashi_vault.vault_database_static_role_delete:
    url: https://vault:8201
    auth_method: userpass
    username: '{{ user }}'
    password: '{{ passwd }}'
    role_name: SomeStaticRole
  register: result

- name: Display the result of the operation
  ansible.builtin.debug:
    msg: "{{ result }}"

- name: Delete a static role with a custom mount point
  community.hashi_vault.vault_database_static_role_delete:
    url: https://vault:8201
    auth_method: userpass
    username: '{{ user }}'
    password: '{{ passwd }}'
    engine_mount_path: db1
    role_name: SomeStaticRole
  register: result

- name: Display the result of the operation
  ansible.builtin.debug:
    msg: "{{ result }}"
"""

RETURN = r""""""

import traceback

from ansible.module_utils.common.text.converters import to_text

from ..module_utils._hashi_vault_module import HashiVaultModule
from ..module_utils._hashi_vault_common import HashiVaultValueError


def run_module():
    argspec = HashiVaultModule.generate_argspec(
        engine_mount_point=dict(type="str", required=False),
        role_name=dict(type="str", required=True),
    )

    module = HashiVaultModule(argument_spec=argspec, supports_check_mode=True)

    if module.check_mode is True:
        module.exit_json(changed=True)

    parameters = {}
    engine_mount_point = module.params.get("engine_mount_point", None)
    if engine_mount_point is not None:
        parameters["mount_point"] = engine_mount_point
    parameters["name"] = module.params.get("role_name")

    module.connection_options.process_connection_options()
    client_args = module.connection_options.get_hvac_connection_options()
    client = module.helper.get_vault_client(**client_args)
    hvac_exceptions = module.helper.get_hvac().exceptions

    try:
        module.authenticator.validate()
        module.authenticator.authenticate(client)
    except (NotImplementedError, HashiVaultValueError) as e:
        module.fail_json(msg=to_text(e), exception=traceback.format_exc())

    try:
        client.secrets.database.delete_static_role(**parameters)
    except hvac_exceptions.Forbidden as e:
        module.fail_json(
            msg="Forbidden: Permission Denied to path ['%s']."
            % (engine_mount_point or "database"),
            exception=traceback.format_exc(),
        )
    except hvac_exceptions.InvalidPath as e:
        module.fail_json(
            msg="Invalid or missing path ['%s/static-roles/%s']."
            % (engine_mount_point or "database", parameters["name"]),
            exception=traceback.format_exc(),
        )
    else:
        module.exit_json(changed=True)


def main():
    run_module()


if __name__ == "__main__":
    main()
