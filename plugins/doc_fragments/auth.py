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
          - C(cert) auth method was added in collection version C(1.4.0).
        choices:
          - token
          - userpass
          - ldap
          - approle
          - aws_iam_login
          - jwt
          - cert
          - none
        default: token
        type: str
      mount_point:
        description:
          - Vault mount point.
          - If not specified, the default mount point for a given auth method is used.
          - Does not apply to token authentication.
        type: str
      token:
        description:
          - Vault token. Token may be specified explicitly, through the listed [env] vars, and also through the C(VAULT_TOKEN) env var.
          - If no token is supplied, explicitly or through env, then the plugin will check for a token file, as determined by I(token_path) and I(token_file).
          - The order of token loading (first found wins) is C(token param -> ansible var -> ANSIBLE_HASHI_VAULT_TOKEN -> VAULT_TOKEN -> token file).
        type: str
      token_path:
        description: If no token is specified, will try to read the I(token_file) from this path.
        type: str
      token_file:
        description: If no token is specified, will try to read the token from this file in I(token_path).
        default: '.vault-token'
        type: str
      token_validate:
        description:
          - For token auth, will perform a C(lookup-self) operation to determine the token's validity before using it.
          - Disable if your token does not have the C(lookup-self) capability.
        type: bool
        default: true
        version_added: 0.2.0
      username:
        description: Authentication user name.
        type: str
      password:
        description: Authentication password.
        type: str
      role_id:
        description:
          - Vault Role ID or name. Used in C(approle), C(aws_iam_login), and C(cert) auth methods.
          - For C(cert) auth, if no I(role_id) is supplied, the default behavior is to try all certificate roles and return any one that matches.
        type: str
      secret_id:
        description: Secret ID to be used for Vault AppRole authentication.
        type: str
      jwt:
        description: The JSON Web Token (JWT) to use for JWT authentication to Vault.
        type: str
      aws_profile:
        description: The AWS profile
        type: str
        aliases: [ boto_profile ]
      aws_access_key:
        description: The AWS access key to use.
        type: str
        aliases: [ aws_access_key_id ]
      aws_secret_key:
        description: The AWS secret key that corresponds to the access key.
        type: str
        aliases: [ aws_secret_access_key ]
      aws_security_token:
        description: The AWS security token if using temporary access and secret keys.
        type: str
      region:
        description: The AWS region for which to create the connection.
        type: str
      aws_iam_server_id:
        description: If specified, sets the value to use for the C(X-Vault-AWS-IAM-Server-ID) header as part of C(GetCallerIdentity) request.
        required: False
        type: str
        version_added: '0.2.0'
      cert_auth_public_key:
        description: For C(cert) auth, path to the certificate file to authenticate with, in PEM format.
        type: path
        version_added: 1.4.0
      cert_auth_private_key:
        description: For C(cert) auth, path to the private key file to authenticate with, in PEM format.
        type: path
        version_added: 1.4.0
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
          - section: hashi_vault_collection
            key: auth_method
            version_added: 1.4.0
        vars:
          - name: ansible_hashi_vault_auth_method
            version_added: 1.2.0
      mount_point:
        env:
          - name: ANSIBLE_HASHI_VAULT_MOUNT_POINT
            version_added: 1.5.0
        ini:
          - section: hashi_vault_collection
            key: mount_point
            version_added: 1.5.0
        vars:
          - name: ansible_hashi_vault_mount_point
            version_added: 1.5.0
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
          - section: hashi_vault_collection
            key: token_path
            version_added: 1.4.0
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
          - section: hashi_vault_collection
            key: token_file
            version_added: 1.4.0
        vars:
          - name: ansible_hashi_vault_token_file
            version_added: 1.2.0
      token_validate:
        env:
          - name: ANSIBLE_HASHI_VAULT_TOKEN_VALIDATE
        ini:
          - section: hashi_vault_collection
            key: token_validate
            version_added: 1.4.0
        vars:
          - name: ansible_hashi_vault_token_validate
            version_added: 1.2.0
      username:
        env:
          - name: ANSIBLE_HASHI_VAULT_USERNAME
            version_added: '1.2.0'
        vars:
          - name: ansible_hashi_vault_username
            version_added: '1.2.0'
      password:
        env:
          - name: ANSIBLE_HASHI_VAULT_PASSWORD
            version_added: '1.2.0'
        vars:
          - name: ansible_hashi_vault_password
            version_added: '1.2.0'
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
          - section: hashi_vault_collection
            key: role_id
            version_added: 1.4.0
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
      aws_profile:
        env:
          - name: AWS_DEFAULT_PROFILE
          - name: AWS_PROFILE
      aws_access_key:
        env:
          - name: EC2_ACCESS_KEY
          - name: AWS_ACCESS_KEY
          - name: AWS_ACCESS_KEY_ID
      aws_secret_key:
        env:
          - name: EC2_SECRET_KEY
          - name: AWS_SECRET_KEY
          - name: AWS_SECRET_ACCESS_KEY
      aws_security_token:
        env:
          - name: EC2_SECURITY_TOKEN
          - name: AWS_SESSION_TOKEN
          - name: AWS_SECURITY_TOKEN
      region:
        env:
          - name: EC2_REGION
          - name: AWS_REGION
      aws_iam_server_id:
        env:
          - name: ANSIBLE_HASHI_VAULT_AWS_IAM_SERVER_ID
        ini:
          - section: hashi_vault_collection
            key: aws_iam_server_id
            version_added: 1.4.0
      cert_auth_public_key:
        env:
          - name: ANSIBLE_HASHI_VAULT_CERT_AUTH_PUBLIC_KEY
        ini:
          - section: hashi_vault_collection
            key: cert_auth_public_key
      cert_auth_private_key:
        env:
          - name: ANSIBLE_HASHI_VAULT_CERT_AUTH_PRIVATE_KEY
        ini:
          - section: hashi_vault_collection
            key: cert_auth_private_key
    '''
