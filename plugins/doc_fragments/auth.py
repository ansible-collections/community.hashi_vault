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
      token:
        description:
          - Vault token. Token may be specified explicitly, through the listed [env] vars, and also through the C(VAULT_TOKEN) env var.
          - If no token is supplied, explicitly or through env, then the plugin will check for a token file, as determined by I(token_path) and I(token_file).
          - The order of token loading (first found wins) is C(token param -> ansible var -> ANSIBLE_HASHI_VAULT_TOKEN -> VAULT_TOKEN -> token file).
      token_path:
        description: If no token is specified, will try to read the I(token_file) from this path.
      token_file:
        description: If no token is specified, will try to read the token from this file in I(token_path).
        default: '.vault-token'
      token_validate:
        description:
          - For token auth, will perform a C(lookup-self) operation to determine the token's validity before using it.
          - Disable if your token does not have the C(lookup-self) capability.
        type: boolean
        default: true
        version_added: 0.2.0
      role_id:
        description: Vault Role ID. Used in approle and aws_iam_login auth methods.
      secret_id:
        description: Secret ID to be used for Vault AppRole authentication.
      jwt:
        description: The JSON Web Token (JWT) to use for JWT authentication to Vault.
    '''

    PLUGINS = r'''
    options:
      auth_method:
        env:
          - name: VAULT_AUTH_METHOD
            deprecated:
              why: standardizing environment variables
              version: 2.0.0
              collection_name: community.hashi_vault
              alternatives: ANSIBLE_HASHI_VAULT_AUTH_METHOD
          - name: ANSIBLE_HASHI_VAULT_AUTH_METHOD
            version_added: 0.2.0
        ini:
          - section: lookup_hashi_vault
            key: auth_method
        vars:
          - name: ansible_hashi_vault_auth_method
            version_added: 1.2.0
      token:
        env:
          - name: ANSIBLE_HASHI_VAULT_TOKEN
            version_added: 0.2.0
        vars:
          - name: ansible_hashi_vault_token
            version_added: 1.2.0
      token_path:
        env:
          - name: VAULT_TOKEN_PATH
            deprecated:
              why: standardizing environment variables
              version: 2.0.0
              collection_name: community.hashi_vault
              alternatives: ANSIBLE_HASHI_VAULT_TOKEN_PATH
          - name: ANSIBLE_HASHI_VAULT_TOKEN_PATH
            version_added: 0.2.0
        ini:
          - section: lookup_hashi_vault
            key: token_path
        vars:
          - name: ansible_hashi_vault_token_path
            version_added: 1.2.0
      token_file:
        env:
          - name: VAULT_TOKEN_FILE
            deprecated:
              why: standardizing environment variables
              version: 2.0.0
              collection_name: community.hashi_vault
              alternatives: ANSIBLE_HASHI_VAULT_TOKEN_FILE
          - name: ANSIBLE_HASHI_VAULT_TOKEN_FILE
            version_added: 0.2.0
        ini:
          - section: lookup_hashi_vault
            key: token_file
        vars:
          - name: ansible_hashi_vault_token_file
            version_added: 1.2.0
      token_validate:
        env:
          - name: ANSIBLE_HASHI_VAULT_TOKEN_VALIDATE
        ini:
          - section: lookup_hashi_vault
            key: token_validate
        vars:
          - name: ansible_hashi_vault_token_validate
            version_added: 1.2.0
      role_id:
        env:
          - name: VAULT_ROLE_ID
            deprecated:
              why: standardizing environment variables
              version: 2.0.0
              collection_name: community.hashi_vault
              alternatives: ANSIBLE_HASHI_VAULT_ROLE_ID
          - name: ANSIBLE_HASHI_VAULT_ROLE_ID
            version_added: 0.2.0
        ini:
          - section: lookup_hashi_vault
            key: role_id
        vars:
          - name: ansible_hashi_vault_role_id
            version_added: 1.2.0
      secret_id:
        env:
          - name: VAULT_SECRET_ID
            deprecated:
              why: standardizing environment variables
              version: 2.0.0
              collection_name: community.hashi_vault
              alternatives: ANSIBLE_HASHI_VAULT_SECRET_ID
          - name: ANSIBLE_HASHI_VAULT_SECRET_ID
            version_added: 0.2.0
        vars:
          - name: ansible_hashi_vault_secret_id
            version_added: 1.2.0
      jwt:
        env:
          - name: ANSIBLE_HASHI_VAULT_JWT
    '''
