# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    DOCUMENTATION = r'''
    options:
      auth_method:
        description:
          - Authentication method to be used.
          - C(none) auth method was added in collection version C(1.2.0).
        env:
          - name: VAULT_AUTH_METHOD
            deprecated:
              why: standardizing environment variables
              version: 2.0.0
              collection_name: community.hashi_vault
              alternatives: ANSIBLE_HASHI_VAULT_AUTH_METHOD
          - name: ANSIBLE_HASHI_VAULT_AUTH_METHOD
            version_added: '0.2.0'
        ini:
          - section: lookup_hashi_vault
            key: auth_method
        vars:
          - name: ansible_hashi_vault_auth_method
            version_added: '1.2.0'
        choices:
          - token
          - userpass
          - ldap
          - approle
          - aws_iam_login
          - jwt
          - none
        default: token
      mount_point:
        description:
          - Vault mount point.
          - If not specified, the default mount point for a given auth method is used.
          - Does not apply to token authentication.
    '''
