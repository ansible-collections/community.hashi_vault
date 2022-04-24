# (c) 2022, Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
name: vault_kv2_get
version_added: 2.5.0
author:
  - Brian Scholer (@briantist)
short_description: Get a secret from HashiCorp Vault's KV version 2 secret store
requirements:
  - C(hvac) (L(Python library,https://hvac.readthedocs.io/en/stable/overview.html))
  - For detailed requirements, see R(the collection requirements page,ansible_collections.community.hashi_vault.docsite.user_guide.requirements).
description:
  - Gets a secret from HashiCorp Vault's KV version 2 secret store.
seealso:
  - module: community.hashi_vault.vault_kv2_get
  - ref: community.hashi_vault.vault_kv1_get lookup <ansible_collections.community.hashi_vault.vault_kv1_get_lookup>
    description: The official documentation for the C(community.hashi_vault.vault_kv1_get) lookup plugin.
  - module: community.hashi_vault.vault_kv1_get
  - ref: community.hashi_vault Lookup Guide <ansible_collections.community.hashi_vault.docsite.lookup_guide>
    description: Guidance on using lookups in C(community.hashi_vault).
  - name: KV2 Secrets Engine
    description: Documentation for the Vault KV secrets engine, version 2.
    link: https://www.vaultproject.io/docs/secrets/kv/kv-v2
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
  version:
    description: Specifies the version to return. If not set the latest version is returned.
    type: int
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
          data:
            Key1: value1
            Key2: value2
          metadata:
            created_time: "2022-04-21T15:56:58.8525402Z"
            custom_metadata": null
            deletion_time": ""
            destroyed": false
            version": 2
        lease_duration: 0
        lease_id: ""
        renewable: false
        request_id: dc829675-9119-e831-ae74-35fc5d33d200
        warnings: null
        wrap_info: null
    data:
      description: The C(data) field of raw result. This can also be accessed via C(raw.data).
      returned: success
      type: dict
      sample:
        data:
          Key1: value1
          Key2: value2
        metadata:
          created_time: "2022-04-21T15:56:58.8525402Z"
          custom_metadata": null
          deletion_time": ""
          destroyed": false
          version": 2
    secret:
      description: The C(data) field within the C(data) field. Equivalent to C(raw.data.data).
      returned: success
      type: dict
      sample:
        Key1: value1
        Key2: value2
    metadata:
      description: The C(metadata) field within the C(data) field. Equivalent to C(raw.data.metadata).
      returned: success
      type: dict
      sample:
        created_time: "2022-04-21T15:56:58.8525402Z"
        custom_metadata": null
        deletion_time": ""
        destroyed": false
        version": 2
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
        version = self._options_adapter.get_option_default('version')

        try:
            self.authenticator.validate()
            self.authenticator.authenticate(client)
        except (NotImplementedError, HashiVaultValueError) as e:
            raise AnsibleError(e)

        for term in terms:
            try:
                raw = client.secrets.kv.v2.read_secret_version(path=term, version=version, mount_point=backend_mount_point)
            except hvac.exceptions.Forbidden as e:
                raise_from(AnsibleError("Forbidden: Permission Denied to path ['%s']." % term), e)
            except hvac.exceptions.InvalidPath as e:
                raise_from(
                    AnsibleError("Invalid or missing path ['%s'] with secret version '%s'. Check the path or secret version." % (term, version or 'latest')),
                    e
                )

            data = raw['data']
            metadata = data['metadata']
            secret = data['data']

            ret.append(dict(raw=raw, data=data, secret=secret, metadata=metadata))

        return ret
