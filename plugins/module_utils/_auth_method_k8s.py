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

from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import HashiVaultAuthMethodBase


class HashiVaultAuthMethodK8S(HashiVaultAuthMethodBase):
    '''HashiVault option group class for auth: k8s'''

    NAME = 'k8s'
    OPTIONS = ['jwt', 'role_id', 'mount_point']

    def __init__(self, option_adapter, warning_callback):
        super(HashiVaultAuthMethodK8S, self).__init__(option_adapter, warning_callback)

    def validate(self):
        self.validate_by_required_fields('role_id')

    def authenticate(self, client, use_token=True):
        params = self._options.get_filled_options(*self.OPTIONS)
        if not params.get('jwt'):
            # Mode in cluster fetch jwt in pods
            try:
                f = open('/var/run/secrets/kubernetes.io/serviceaccount/token')
                jwt = f.read()
                params['jwt'] = jwt
            except:
                raise NotImplementedError("Can't read jwt in /var/run/secrets/kubernetes.io/serviceaccount/token")
        params['role'] = params.pop('role_id')
        
        try:
            response = client.auth_kubernetes(**params)
        except (NotImplementedError, AttributeError):
            raise NotImplementedError("K8S authentication requires HVAC version 0.8.0 or higher.")

        return response
