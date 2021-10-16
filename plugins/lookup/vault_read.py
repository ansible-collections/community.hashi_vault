# (c) 2021, Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
  lookup: vault_read
  version_added: 1.4.0
  author:
    - Brian Scholer (@briantist)
  short_description: Perform a read operation against HashiCorp Vault
  requirements:
    - hvac (python library)
    - hvac 0.7.0+ (for namespace support)
    - hvac 0.9.6+ (to avoid most deprecation warnings)
    - hvac 0.10.5+ (for JWT auth)
    - hvac 0.10.6+ (to avoid deprecation warning for AppRole)
    - botocore (only if inferring aws params from boto)
    - boto3 (only if using a boto profile)
  description:
    - Performs a generic read operation against a given path in HashiCorp Vault.
  notes:
    - ???
  extends_documentation_fragment:
    - community.hashi_vault.connection
    - community.hashi_vault.connection.plugins
    - community.hashi_vault.auth
    - community.hashi_vault.auth.plugins
  options:
    _terms:
      description: Vault path(s) to be read.
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
    - the raw result of the read against the given path.
  type: list
  elements: dict
"""

from ansible.errors import AnsibleError
from ansible.utils.display import Display

from ansible_collections.community.hashi_vault.plugins.plugin_utils._hashi_vault_lookup_base import HashiVaultLookupBase

display = Display()

HAS_HVAC = False
try:
    import hvac
    HAS_HVAC = True
except ImportError:
    HAS_HVAC = False


class LookupModule(HashiVaultLookupBase):
    def run(self, terms, variables=None, **kwargs):
        if not HAS_HVAC:
            raise AnsibleError("Please pip install hvac to use the vault_read lookup.")

        ret = []

        self.set_options(direct=kwargs, var_options=variables)
        # TODO: remove process_deprecations() if backported fix is available (see method definition)
        self.process_deprecations()

        self.connection_options.process_connection_options()
        client_args = self.connection_options.get_hvac_connection_options()
        client = self.helper.get_vault_client(**client_args)

        try:
            self.authenticator.validate()
            self.authenticator.authenticate(client)
        except NotImplementedError as e:
            raise AnsibleError(e)

        for term in terms:
            try:
                data = client.read(term)
            except hvac.exceptions.Forbidden:
                # raise AnsibleError('term (%s): |%r|' % (str(type(term)), term))
                raise AnsibleError("Forbidden: Permission Denied to path '%s'." % term)

            if data is None:
                raise AnsibleError("The path '%s' doesn't seem to exist." % term)

            ret.append(data)

        return ret
