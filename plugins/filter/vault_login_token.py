# -*- coding: utf-8 -*-
# (c) 2021, Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
  name: vault_login_token
  short_description: Extract the token value from the structure returned by a Vault login operation
  version_added: 2.2.0
  author: Brian Scholer (@briantist)
  description:
    - Extracts the token value from the structure returned by a Vault login operation, such as those returned by the M(community.hashi_vault.vault_login)
      or R(lookup pugin, ansible_collections.community.hashi_vault.vault_login_lookup).
  options:
    _input:
      description:
        - The login response to extract the token from.
      type: dict
      required: true
    optional_field:
      description:
        - If a field of this name exists in the input dictionary, then the value of that field is taken the be the login response,
          rather than the input dictionary itself.
        - The purpose of this option is primarily to deal with the difference between the output of the lookup plugin (which returns
          the login response directly) and the module, which returns the login response in a C(login) field in its return.
      type: str
      default: login
'''

EXAMPLES = '''
# Combine with login lookup

- name: Perform a login with a lookup and display the token
  vars:
    login_response: "{{ lookup('community.hashi_vault.vault_login') }}"
  ansible.builtin.debug:
    msg: "The token is {{ login_response | community.hashi_vault.vault_login_token }}"


# Combine with login module

- name: Perform a login with a module
  community.hashi_vault.vault_login:
  register: login_response

- name: Display the token
  ansible.builtin.debug:
    msg: "The token is {{ login_response | community.hashi_vault.vault_login_token }}"
'''

RETURN = '''
_value:
  description: The login token.
  type: string
'''

from ansible.errors import AnsibleError


def vault_login_token(login_response, optional_field='login'):
    '''Extracts the token value from a Vault login response.
    Meant to be used with the vault_login module and lookup plugin.
    '''

    try:
        deref = login_response[optional_field]
    except TypeError:
        raise AnsibleError("The 'vault_login_token' filter expects a dictionary.")
    except KeyError:
        deref = login_response

    try:
        token = deref['auth']['client_token']
    except KeyError:
        raise AnsibleError("Could not find 'auth' or 'auth.client_token' fields. Input may not be a Vault login response.")

    return token


class FilterModule(object):
    '''Ansible jinja2 filters'''

    def filters(self):
        return {
            'vault_login_token': vault_login_token,
        }
