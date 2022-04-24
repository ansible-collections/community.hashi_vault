# (c) 2022, Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
name: vault_kv1_get
version_added: 2.5.0
author:
  - Brian Scholer (@briantist)
short_description: Get a secret from HashiCorp Vault's KV version 1 secret store
requirements:
  - C(hvac) (L(Python library,https://hvac.readthedocs.io/en/stable/overview.html))
  - For detailed requirements, see R(the collection requirements page,ansible_collections.community.hashi_vault.docsite.user_guide.requirements).
description:
  - Gets a secret from HashiCorp Vault's KV version 1 secret store.
seealso:
  - module: community.hashi_vault.vault_kv1_get
  - ref: community.hashi_vault.vault_kv2_get lookup <ansible_collections.community.hashi_vault.vault_kv2_get_lookup>
    description: The official documentation for the C(community.hashi_vault.vault_kv2_get) lookup plugin.
  - module: community.hashi_vault.vault_kv2_get
  - name: KV1 Secrets Engine
    description: Documentation for the Vault KV secrets engine, version 1.
    link: https://www.vaultproject.io/docs/secrets/kv/kv-v1
extends_documentation_fragment:
  - community.hashi_vault.connection
  - community.hashi_vault.connection.plugins
  - community.hashi_vault.auth
  - community.hashi_vault.auth.plugins
  - community.hashi_vault.backend_mount
  - community.hashi_vault.backend_mount.plugins
options:
  _terms:
    description:
      - Vault KV path(s) to be read.
      - These are relative to the I(backend_mount_point), so the mount path should not be included.
    type: str
    required: True
  backend_mount_point:
    default: kv
'''

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

RETURN = r'''
_raw:
  description:
    - The result of the read(s) against the given path(s).
  type: list
  elements: dict
  contains:
    raw:
      description: The raw result of the read against the given path.
      returned: success
      type: dict
      sample:
        auth: null
        data:
          Key1: value1
          Key2: value2
        lease_duration: 2764800
        lease_id: ""
        renewable: false
        request_id: e99f145f-f02a-7073-1229-e3f191057a70
        warnings: null
        wrap_info: null
    data:
      description: The C(data) field of raw result. This can also be accessed via C(raw.data).
      returned: success
      type: dict
      sample:
        Key1: value1
        Key2: value2
    secret:
      description: The C(data) field of the raw result. This is identical to C(data) in the return values.
      returned: success
      type: dict
      sample:
        Key1: value1
        Key2: value2
    metadata:
      description: This is a synthetic result. It is the same as C(raw) with C(data) removed.
      returned: success
      type: dict
      sample:
        auth: null
        lease_duration: 2764800
        lease_id: ""
        renewable: false
        request_id: e99f145f-f02a-7073-1229-e3f191057a70
        warnings: null
        wrap_info: null
'''

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

        backend_mount_point = self._options_adapter.get_option('backend_mount_point')

        try:
            self.authenticator.validate()
            self.authenticator.authenticate(client)
        except (NotImplementedError, HashiVaultValueError) as e:
            raise AnsibleError(e)

        for term in terms:
            try:
                raw = client.secrets.kv.v1.read_secret(path=term, mount_point=backend_mount_point)
            except hvac.exceptions.Forbidden as e:
                raise_from(AnsibleError("Forbidden: Permission Denied to path ['%s']." % term), e)
            except hvac.exceptions.InvalidPath as e:
                if 'Invalid path for a versioned K/V secrets engine' in str(e):
                    msg = "Invalid path for a versioned K/V secrets engine ['%s']. If this is a KV version 2 path, use community.hashi_vault.vault_kv2_get."
                else:
                    msg = "Invalid or missing path ['%s']."

                raise_from(AnsibleError(msg % (term,)), e)

            metadata = raw.copy()
            data = metadata.pop('data')

            ret.append(dict(raw=raw, data=data, secret=data, metadata=metadata))

        return ret
