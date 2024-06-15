#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2024, Martin Chmielewski (@M4rt1nCh)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
module: vault_database_static_role_rotate_credentials
version_added: 6.2.0
author:
  - Martin Chmielewski (@M4rt1nCh)
short_description: Trigger the credential rotation for a static role
requirements:
  - C(hvac) (L(Python library,https://hvac.readthedocs.io/en/stable/overview.html)) >= 2.0.0
  - For detailed requirements, see R(the collection requirements page,ansible_collections.community.hashi_vault.docsite.user_guide.requirements).
description:
  - This endpoint is used to
  - L(rotate the Static Role credentials,https://hvac.readthedocs.io/en/stable/usage/secrets_engines/database.html#rotate-static-role-credentials)
  - stored for a given role name. While Static Roles are rotated automatically by Vault at configured rotation periods,
  - users can use this endpoint to manually trigger a rotation to change the stored password and reset the TTL of the Static Role's password.
notes:
  - This module always reports C(changed) status because it cannot guarantee idempotence.
  - Use C(changed_when) to control that in cases where the operation is known to not change state.
attributes:
  check_mode:
    support: partial
    details:
      - In check mode, a sample response will be returned, but the credential rotation will not be performed in Hashicorp Vault.
extends_documentation_fragment:
  - community.hashi_vault.attributes
  - community.hashi_vault.attributes.action_group
  - community.hashi_vault.connection
  - community.hashi_vault.auth
  - community.hashi_vault.engine_mount
options:
  role_name:
    description: The name of the role to rotate credentials for.
    type: str
    required: True
"""

EXAMPLES = r"""
- name: Rotate credentials of a static role with the default mount point
  community.hashi_vault.vault_database_static_role_rotate_credentials:
    url: https://vault:8201
    auth_method: userpass
    username: '{{ user }}'
    password: '{{ passwd }}'
    role_name: SomeRole
  register: result

- name: Display the result of the operation
  ansible.builtin.debug:
    msg: "{{ result }}"

- name: Rotate credentials of a static role with a custom mount point
  community.hashi_vault.vault_database_static_role_rotate_credentials:
    url: https://vault:8201
    auth_method: userpass
    username: '{{ user }}'
    password: '{{ passwd }}'
    engine_mount_point: db1
    role_name: SomeRole
  register: result

- name: Display the result of the operation
  ansible.builtin.debug:
    msg: "{{ result }}"
"""

RETURN = r""""""

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
        role_name=dict(type="str", required=True),
    )

    module = HashiVaultModule(argument_spec=argspec, supports_check_mode=True)

    if not HAS_HVAC:
        module.fail_json(msg=missing_required_lib("hvac"), exception=HVAC_IMPORT_ERROR)

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

    try:
        module.authenticator.validate()
        module.authenticator.authenticate(client)
    except (NotImplementedError, HashiVaultValueError) as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    try:
        raw = client.secrets.database.rotate_static_role_credentials(**parameters)
    except AttributeError as e:
        module.fail_json(
            msg="hvac>=2.0.0 is required", exception=traceback.format_exc()
        )
    except hvac.exceptions.Forbidden as e:
        module.fail_json(
            msg="Forbidden: Permission Denied to path ['%s']." % engine_mount_point
            or "database",
            exception=traceback.format_exc(),
        )
    except hvac.exceptions.InvalidPath as e:
        module.fail_json(
            msg="Invalid or missing path ['%s/rotate-role/%s']."
            % (engine_mount_point or "database", parameters["name"]),
            exception=traceback.format_exc(),
        )
    else:
        module.exit_json(changed=True)


def main():
    run_module()


if __name__ == "__main__":
    main()
