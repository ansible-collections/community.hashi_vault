# (c) 2021, Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
  lookup: vault_login
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
    - module: community.hashi_vault.vault_login
  notes:
    - This lookup does not use the term string and will not work correctly in loops. Only a single response will be returned.
    - The C(none) auth method is not valid for this plugin because there is no response to return.
    - "With C(token) auth, no actual login is performed.
      Instead, the given token's additional information is returned in a structure that resembles what login responses look like."
    - "The C(token) auth method will only return full information if I(token_validate=True).
      If the token does not have the C(lookup-self) capability, this will fail. If I(token_validate=False), only the token value itself
      will be returned in the structure."
  extends_documentation_fragment:
    - community.hashi_vault.connection
    - community.hashi_vault.connection.plugins
    - community.hashi_vault.auth
    - community.hashi_vault.auth.plugins
  options:
    _terms:
      description: This is unused and should be an empty string.
      type: str
      required: True
"""

EXAMPLES = """
- name: Read a kv2 secret
  ansible.builtin.debug:
    msg: "{{ lookup('community.hashi_vault.vault_read', 'secret/data/hello', url='https://vault:8201') }}"

- name: Retrieve an approle role ID
  ansible.builtin.debug:
    msg: "{{ lookup('community.hashi_vault.vault_read', 'auth/approle/role/role-name/role-id', url='https://vault:8201') }}"

- name: Perform multiple reads with a single Vault login
  vars:
    paths:
      - secret/data/hello
      - auth/approle/role/role-one/role-id
      - auth/approle/role/role-two/role-id
  ansible.builtin.debug:
    msg: "{{ lookup('community.hashi_vault.vault_read', *paths, auth_method='userpass', username=user, password=pwd) }}"

- name: Perform multiple reads with a single Vault login in a loop
  vars:
    paths:
      - secret/data/hello
      - auth/approle/role/role-one/role-id
      - auth/approle/role/role-two/role-id
  ansible.builtin.debug:
    msg: '{{ item }}'
  loop: "{{ query('community.hashi_vault.vault_read', *paths, auth_method='userpass', username=user, password=pwd) }}"

- name: Perform multiple reads with a single Vault login in a loop (via with_)
  vars:
    ansible_hashi_vault_auth_method: userpass
    ansible_hashi_vault_username: '{{ user }}'
    ansible_hashi_vault_passowrd: '{{ pwd }}'
  ansible.builtin.debug:
    msg: '{{ item }}'
  with_community.hashi_vault.vault_read:
    - secret/data/hello
    - auth/approle/role/role-one/role-id
    - auth/approle/role/role-two/role-id
"""

RETURN = """
_raw:
  description:
    - The result of the login with the given auth method.
  type: list
  elements: dict
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

from ansible.errors import AnsibleError
from ansible.utils.display import Display

from ansible_collections.community.hashi_vault.plugins.plugin_utils._hashi_vault_lookup_base import HashiVaultLookupBase
from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import HashiVaultValueError

display = Display()


class LookupModule(HashiVaultLookupBase):
    def run(self, terms, variables=None, **kwargs):

        self.set_options(direct=kwargs, var_options=variables)
        # TODO: remove process_deprecations() if backported fix is available (see method definition)
        self.process_deprecations()

        if self.get_option('auth_method') == 'none':
            raise AnsibleError("The 'none' auth method is not valid for this lookup.")

        self.connection_options.process_connection_options()
        client_args = self.connection_options.get_hvac_connection_options()
        client = self.helper.get_vault_client(**client_args)

        if len(terms) > 1:
            display.warning("Multiple terms were supplied and will be ignored. This lookup does not use term strings.")

        if len(terms[0]) > 0:
            display.warning("Supplied term string '%s' will be ignored. This lookup does not use term strings." % (terms[0],))

        try:
            self.authenticator.validate()
            response = self.authenticator.authenticate(client)
        except (NotImplementedError, HashiVaultValueError) as e:
            raise AnsibleError(e)

        return [response]
