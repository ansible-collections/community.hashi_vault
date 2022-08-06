# -*- coding: utf-8 -*-
# Copyright (c) 2021 Devon Mar (@devon-mar)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible_collections.community.hashi_vault.tests.unit.compat import mock

from ansible_collections.community.hashi_vault.plugins.module_utils._auth_method_cert import (
    HashiVaultAuthMethodCert,
)

from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import (
    HashiVaultAuthMethodBase,
    HashiVaultValueError,
)


@pytest.fixture
def auth_cert(adapter, warner, deprecator):
    return HashiVaultAuthMethodCert(adapter, warner, deprecator)


@pytest.fixture
def cert_login_response(fixture_loader):
    return fixture_loader("cert_login_response.json")


class TestAuthCert(object):

    def test_auth_cert_is_auth_method_base(self, auth_cert):
        assert isinstance(auth_cert, HashiVaultAuthMethodCert)
        assert issubclass(HashiVaultAuthMethodCert, HashiVaultAuthMethodBase)

    def test_auth_cert_validate_direct(self, auth_cert, adapter):
        adapter.set_option("cert_auth_public_key", "/fake/path")
        adapter.set_option("cert_auth_private_key", "/fake/path")

        auth_cert.validate()

    @pytest.mark.parametrize("opt_patch", [
        {},
        {"cert_auth_public_key": ""},
        {"cert_auth_private_key": ""},
        {"mount_point": ""}
    ])
    def test_auth_cert_validate_xfailures(self, auth_cert, adapter, opt_patch):
        adapter.set_options(**opt_patch)

        with pytest.raises(HashiVaultValueError, match=r"Authentication method cert requires options .*? to be set, but these are missing:"):
            auth_cert.validate()

    @pytest.mark.parametrize("use_token", [True, False], ids=lambda x: "use_token=%s" % x)
    @pytest.mark.parametrize("mount_point", [None, "other"], ids=lambda x: "mount_point=%s" % x)
    @pytest.mark.parametrize("role_id", [None, "cert"], ids=lambda x: "role_id=%s" % x)
    def test_auth_cert_authenticate(self, auth_cert, client, adapter, mount_point, use_token, role_id,
                                    cert_login_response):
        adapter.set_option("cert_auth_public_key", "/fake/path")
        adapter.set_option("cert_auth_private_key", "/fake/path")
        adapter.set_option("role_id", role_id)
        adapter.set_option("mount_point", mount_point)

        expected_login_params = {
            "cert_pem": "/fake/path",
            "key_pem": "/fake/path",
            "use_token": use_token,
        }

        if role_id:
            expected_login_params["name"] = role_id

        if mount_point:
            expected_login_params["mount_point"] = mount_point

        def _set_client_token(*args, **kwargs):
            if kwargs['use_token']:
                client.token = cert_login_response['auth']['client_token']
            return cert_login_response

        with mock.patch.object(client.auth.cert, "login", side_effect=_set_client_token) as cert_login:
            response = auth_cert.authenticate(client, use_token=use_token)
            cert_login.assert_called_once_with(**expected_login_params)

        assert response["auth"]["client_token"] == cert_login_response["auth"]["client_token"]
        assert (client.token == cert_login_response["auth"]["client_token"]) is use_token
