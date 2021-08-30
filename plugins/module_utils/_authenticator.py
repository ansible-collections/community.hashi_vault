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

# please keep this list in alphabetical order of auth method name
from ansible_collections.community.hashi_vault.plugins.module_utils._auth_method_approle import HashiVaultAuthMethodApprole
from ansible_collections.community.hashi_vault.plugins.module_utils._auth_method_aws_iam_login import HashiVaultAuthMethodAwsIamLogin
from ansible_collections.community.hashi_vault.plugins.module_utils._auth_method_jwt import HashiVaultAuthMethodJwt
from ansible_collections.community.hashi_vault.plugins.module_utils._auth_method_ldap import HashiVaultAuthMethodLdap
from ansible_collections.community.hashi_vault.plugins.module_utils._auth_method_none import HashiVaultAuthMethodNone
from ansible_collections.community.hashi_vault.plugins.module_utils._auth_method_token import HashiVaultAuthMethodToken
from ansible_collections.community.hashi_vault.plugins.module_utils._auth_method_userpass import HashiVaultAuthMethodUserpass


class HashiVaultAuthenticator():
    def __init__(self, option_adapter, warning_callback):
        self._options = option_adapter
        self._selector = {
            # please keep this list in alphabetical order of auth method name
            # so that it's easier to scan and see at a glance that a given auth method is present or absent
            'approle': HashiVaultAuthMethodApprole(option_adapter, warning_callback),
            'aws_iam_login': HashiVaultAuthMethodAwsIamLogin(option_adapter, warning_callback),
            'jwt': HashiVaultAuthMethodJwt(option_adapter, warning_callback),
            'ldap': HashiVaultAuthMethodLdap(option_adapter, warning_callback),
            'none': HashiVaultAuthMethodNone(option_adapter, warning_callback),
            'token': HashiVaultAuthMethodToken(option_adapter, warning_callback),
            'userpass': HashiVaultAuthMethodUserpass(option_adapter, warning_callback),
        }

    def _get_method_object(self, method=None):
        if method is None:
            method = self._options.get_option('auth_method')

        try:
            o_method = self._selector[method]
        except KeyError:
            raise NotImplementedError("auth method '%s' is not implemented in HashiVaultAuthenticator" % method)

        return o_method

    def validate(self, *args, **kwargs):
        method = self._get_method_object(kwargs.pop('method', None))
        method.validate(*args, **kwargs)

    def authenticate(self, *args, **kwargs):
        method = self._get_method_object(kwargs.pop('method', None))
        return method.authenticate(*args, **kwargs)
