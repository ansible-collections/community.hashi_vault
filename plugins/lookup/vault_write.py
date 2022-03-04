# (c) 2022, Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
  name: vault_write
  version_added: 2.4.0
  author:
    - Brian Scholer (@briantist)
  short_description: Perform a write operation against HashiCorp Vault
  requirements:
    - C(hvac) (L(Python library,https://hvac.readthedocs.io/en/stable/overview.html))
    - For detailed requirements, see R(the collection requirements page,ansible_collections.community.hashi_vault.docsite.user_guide.requirements).
  description:
    - Performs a generic write operation against a given path in HashiCorp Vault, returning any output.
  seealso:
    - module: community.hashi_vault.vault_write
    - ref: community.hashi_vault.vault_read lookup <ansible_collections.community.hashi_vault.vault_read_lookup>
      description: The official documentation for the C(community.hashi_vault.vault_read) lookup plugin.
    - module: community.hashi_vault.vault_read
  extends_documentation_fragment:
    - community.hashi_vault.connection
    - community.hashi_vault.connection.plugins
    - community.hashi_vault.auth
    - community.hashi_vault.auth.plugins
  options:
    _terms:
      description: Vault path(s) to be written to.
      type: str
      required: true
    data:
      description: A dictionary to be serialized to JSON and then sent as the request body.
      type: dict
      required: false
      default: {}
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
    ansible_hashi_vault_password: '{{ pwd }}'
  ansible.builtin.debug:
    msg: '{{ item }}'
  with_community.hashi_vault.vault_read:
    - secret/data/hello
    - auth/approle/role/role-one/role-id
    - auth/approle/role/role-two/role-id
"""

RETURN = """
_raw:
  description: The raw result of the write against the given path.
  type: list
  elements: dict
"""

from ansible.errors import AnsibleError
from ansible.utils.display import Display

from ansible.module_utils.six import raise_from

from ansible_collections.community.hashi_vault.plugins.plugin_utils._hashi_vault_lookup_base import HashiVaultLookupBase
from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import HashiVaultValueError

display = Display()

try:
    import hvac
except ImportError as imp_exc:
    HVAC_IMPORT_ERROR = imp_exc
else:
    HVAC_IMPORT_ERROR = None


class LookupModule(HashiVaultLookupBase):
    def run(self, terms, variables=None, **kwargs):
        if HVAC_IMPORT_ERROR:
            raise_from(
                AnsibleError("This plugin requires the 'hvac' Python library"),
                HVAC_IMPORT_ERROR
            )

        ret = []

        self.set_options(direct=kwargs, var_options=variables)
        # TODO: remove process_deprecations() if backported fix is available (see method definition)
        self.process_deprecations()

        self.connection_options.process_connection_options()
        client_args = self.connection_options.get_hvac_connection_options()
        client = self.helper.get_vault_client(**client_args)

        data = self._options_adapter.get_option('data')

        try:
            self.authenticator.validate()
            self.authenticator.authenticate(client)
        except (NotImplementedError, HashiVaultValueError) as e:
            raise AnsibleError(e)

        for term in terms:
            try:
                response = client.write(path=term, **data)
            except hvac.exceptions.Forbidden:
                raise AnsibleError("Forbidden: Permission Denied to path '%s'." % term)
            except hvac.exceptions.InvalidPath:
                raise AnsibleError("The path '%s' doesn't seem to exist." % term)
            except hvac.exceptions.InternalServerError as e:
                raise AnsibleError("Internal Server Error: %s" % str(e))

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
                    display.warning('Vault returned status code %i and an unparsable body.' % response.status_code)
                    output = response.content
            else:
                output = response

            ret.append(output)

        return ret
