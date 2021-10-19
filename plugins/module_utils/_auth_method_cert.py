# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import HashiVaultAuthMethodBase


class HashiVaultAuthMethodCert(HashiVaultAuthMethodBase):
    """HashiVault option group class for auth: cert"""

    NAME = "cert"
    OPTIONS = ["cert_pem", "key_pem", "mount_point", "role_id"]

    def __init__(self, option_adapter, warning_callback):
        super(HashiVaultAuthMethodCert, self).__init__(option_adapter, warning_callback)

    def validate(self):
        self.validate_by_required_fields("cert_pem", "key_pem")

    def authenticate(self, client, use_token=True):
        params = self._options.get_filled_options(*self.OPTIONS)

        if "role_id" in params:
            params["name"] = params.pop("role_id")

        try:
            response = client.auth.cert.login(use_token=use_token, **params)
        except NotImplementedError:
            raise NotImplementedError("cert authentication requires HVAC version 0.10.12 or higher.")

        return response
