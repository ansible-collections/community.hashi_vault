# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

'''Python versions supported: all controller-side versions, all remote-side versions except 2.6'''

# FOR INTERNAL COLLECTION USE ONLY
# The interfaces in this file are meant for use within the community.hashi_vault collection
# and may not remain stable to outside uses. Changes may be made in ANY release, even a bugfix release.
# See also: https://github.com/ansible/community/issues/539#issuecomment-780839686
# Please open an issue if you have questions about this.

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os

from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import (
    HashiVaultAuthMethodBase,
    HashiVaultValueError,
)


class HashiVaultAuthMethodToken(HashiVaultAuthMethodBase):
    '''HashiVault option group class for auth: userpass'''

    NAME = 'token'
    OPTIONS = ['token', 'token_path', 'token_file', 'token_validate']

    def __init__(self, option_adapter, warning_callback):
        super(HashiVaultAuthMethodToken, self).__init__(option_adapter, warning_callback)

    def validate(self):
        if not self._options.get_option('token') and self._options.get_option('token_path'):
            token_filename = os.path.join(
                self._options.get_option('token_path'),
                self._options.get_option('token_file')
            )
            if os.path.exists(token_filename):
                with open(token_filename) as token_file:
                    self._options.set_option('token', token_file.read().strip())

        if not self._options.get_option('token'):
            raise HashiVaultValueError("No Vault Token specified or discovered.")

    def authenticate(self, client, use_token=True):
        token = self._options.get_option('token')
        if use_token:
            client.token = token

            if self._options.get_option('token_validate') and not client.is_authenticated():
                raise HashiVaultValueError("Invalid Vault Token Specified.")

        return token
