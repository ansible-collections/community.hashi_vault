#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2021, Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
  module: vault_login
  version_added: 2.2.0
  author:
    - Brian Scholer (@briantist)
  short_description: Perform a login operation against HashiCorp Vault
  requirements:
    - C(hvac) (L(Python library,https://hvac.readthedocs.io/en/stable/overview.html))
    - For detailed requirements, see R(the collection requirements page,ansible_collections.community.hashi_vault.docsite.user_guide.requirements).
  description:
    - Performs a login operation against a given path in HashiCorp Vault, returning the login response, including the token.
  seealso:
    - ref: community.hashi_vault.vault_login lookup <ansible_collections.community.hashi_vault.vault_login_lookup>
      description: The official documentation for the C(community.hashi_vault.vault_login) lookup plugin.
  extends_documentation_fragment:
    - community.hashi_vault.connection
    - community.hashi_vault.auth
  notes:
    - The C(none) auth method is not valid for this module because there is no response to return.
    - "With C(token) auth, no actual login is performed.
      Instead, the given token's additional information is returned in a structure that resembles what login responses look like."
    - "The C(token) auth method will only return full information if I(token_validate=True).
      If the token does not have the C(lookup-self) capability, this will fail. If I(token_validate=False), only the token value itself
      will be returned in the structure."
  options: {}
"""

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

RETURN = """
login:
  description: The result of the login against the given auth method.
  returned: success
  type: dict
  contains:
    auth:
      description: The C(auth) member of the login response.
      returned: success
      type: dict
      contains:
        client_token:
          description: Contains the token provided by the login operation (or the input token when I(auth_method=token)).
          returned: success
          type: str
    data:
      description: The C(data) member of the login response.
      returned: success, when available
      type: dict
"""

import traceback

from ansible.module_utils._text import to_native

from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_module import HashiVaultModule
from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import HashiVaultValueError


def run_module():
    argspec = HashiVaultModule.generate_argspec(
        # we override this from the shared argspec in order to turn off no_log
        # otherwise we would not be able to return the input token value
        token=dict(type='str', no_log=False, default=None)
    )

    module = HashiVaultModule(
        argument_spec=argspec,
        supports_check_mode=True
    )

    if module.params.get('auth_method') == 'none':
        module.fail_json(msg="The 'none' auth method is not valid for this module.")

    module.connection_options.process_connection_options()
    client_args = module.connection_options.get_hvac_connection_options()
    client = module.helper.get_vault_client(**client_args)

    try:
        module.authenticator.validate()
        response = module.authenticator.authenticate(client)
    except (NotImplementedError, HashiVaultValueError) as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    module.exit_json(login=response)


def main():
    run_module()


if __name__ == '__main__':
    main()
