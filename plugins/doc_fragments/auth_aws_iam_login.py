# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    DOCUMENTATION = r'''
    options:
      aws_profile:
        description: The AWS profile
        type: str
        aliases: [ boto_profile ]
        env:
          - name: AWS_DEFAULT_PROFILE
          - name: AWS_PROFILE
      aws_access_key:
        description: The AWS access key to use.
        type: str
        aliases: [ aws_access_key_id ]
        env:
          - name: EC2_ACCESS_KEY
          - name: AWS_ACCESS_KEY
          - name: AWS_ACCESS_KEY_ID
      aws_secret_key:
        description: The AWS secret key that corresponds to the access key.
        type: str
        aliases: [ aws_secret_access_key ]
        env:
          - name: EC2_SECRET_KEY
          - name: AWS_SECRET_KEY
          - name: AWS_SECRET_ACCESS_KEY
      aws_security_token:
        description: The AWS security token if using temporary access and secret keys.
        type: str
        env:
          - name: EC2_SECURITY_TOKEN
          - name: AWS_SESSION_TOKEN
          - name: AWS_SECURITY_TOKEN
      region:
        description: The AWS region for which to create the connection.
        type: str
        env:
          - name: EC2_REGION
          - name: AWS_REGION
      aws_iam_server_id:
        description: If specified, sets the value to use for the C(X-Vault-AWS-IAM-Server-ID) header as part of C(GetCallerIdentity) request.
        env:
          - name: ANSIBLE_HASHI_VAULT_AWS_IAM_SERVER_ID
        ini:
          - section: lookup_hashi_vault
            key: aws_iam_server_id
        required: False
        version_added: '0.2.0'
    '''
