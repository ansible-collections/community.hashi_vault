#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2020, Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
  module: vault_read
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
    - community.hashi_vault.auth
  options:
    path:
      description: Vault path to be read.
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
    msg: "{{ lookup('community.hashi_vault.vault_read', paths, auth_method='userpass', username=user, password=pwd) }}"

- name: Perform multiple reads with a single Vault login in a loop
  vars:
    paths:
      - secret/data/hello
      - auth/approle/role/role-one/role-id
      - auth/approle/role/role-two/role-id
  ansible.builtin.debug:
    msg: '{{ item }}'
  loop: "{{ query('community.hashi_vault.vault_read', paths, auth_method='userpass', username=user, password=pwd) }}"

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
data:
  description: the raw result of the read against the given path.
  returned: success
  type: dict
"""
import traceback

from ansible.module_utils._text import to_native

from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_module import HashiVaultModule
from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import HashiVaultValueError

HAS_HVAC = False
try:
    import hvac
    HAS_HVAC = True
except ImportError:
    HAS_HVAC = False


def run_module():
    argspec = HashiVaultModule.generate_argspec(
        path=dict(type='str', required=True),
    )

    module = HashiVaultModule(
        argument_spec=argspec,
        supports_check_mode=True
    )

    path = module.params.get('path')

    module.connection_options.process_connection_options()
    client_args = module.connection_options.get_hvac_connection_options()
    client = module.helper.get_vault_client(**client_args)

    try:
        module.authenticator.validate()
        module.authenticator.authenticate(client)
    except (NotImplementedError, HashiVaultValueError) as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    try:
        data = client.read(path)
    except hvac.exceptions.Forbidden as e:
        module.fail_json(msg="Forbidden: Permission Denied to path '%s'." % path, exception=traceback.format_exc())

    if data is None:
        module.fail_json(msg="The path '%s' doesn't seem to exist." % path)

    module.exit_json(data=data)


def main():
    run_module()


if __name__ == '__main__':
    main()
