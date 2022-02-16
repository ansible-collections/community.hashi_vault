# -*- coding: utf-8 -*-
# Copyright (c) 2021 FERREIRA Christophe (@chris93111)
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

'''Python versions supported: >=3.6'''

# FOR INTERNAL COLLECTION USE ONLY
# The interfaces in this file are meant for use within the community.hashi_vault collection
# and may not remain stable to outside uses. Changes may be made in ANY release, even a bugfix release.
# See also: https://github.com/ansible/community/issues/539#issuecomment-780839686
# Please open an issue if you have questions about this.

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import HashiVaultAuthMethodBase, HashiVaultValueError
import os

class HashiVaultAuthMethodKubernetes(HashiVaultAuthMethodBase):
    '''HashiVault option group class for auth: k8s'''

    NAME = 'kubernetes'
    OPTIONS = ['kubernetes_token', 'kubernetes_token_path', 'role_id', 'mount_point']

    def __init__(self, option_adapter, warning_callback):
        super(HashiVaultAuthMethodKubernetes, self).__init__(option_adapter, warning_callback)

    def validate(self):
        self.validate_by_required_fields('role_id')

        if self._options.get_option('kubernetes_token') is None and self._options.get_option('kubernetes_token_path') is not None:
            token_filename = self._options.get_option('kubernetes_token_path')
            if os.path.exists(token_filename):
                if not os.path.isfile(token_filename):
                    raise HashiVaultValueError("The Kubernetes token file '%s' was found but is not a file." % token_filename)
                with open(token_filename) as token_file:
                    self._options.set_option('kubernetes_token', token_file.read().strip())

        if self._options.get_option('kubernetes_token') is None:
            raise HashiVaultValueError(self._options.get_option('kubernetes_token')+self._options.get_option_default('kubernetes_token_path')+"No Kubernetes Token specified or discovered.")

    def authenticate(self, client, use_token=True):
        origin_params = self._options.get_filled_options(*self.OPTIONS)
        params = {"role": origin_params.get('role_id'),
                  "jwt": origin_params.get('kubernetes_token'),
                  "mount_point": origin_params.get('mount_point'),
                  "use_token": use_token}

        try:
            response = client.auth.kubernetes.login(**params)
        except (NotImplementedError, AttributeError):
            self.warn("Kubernetes authentication requires HVAC version 1.0.0 or higher. Deprecated method 'auth_kubernetes' will be used.")
            response = client.auth_kubernetes(**params)
            
        return response
