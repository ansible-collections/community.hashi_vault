# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible_collections.community.hashi_vault.tests.unit.compat import mock

from ansible_collections.community.hashi_vault.plugins.module_utils._auth_method_userpass import (
    HashiVaultAuthMethodUserpass,
)

from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import (
    HashiVaultAuthMethodBase,
    HashiVaultValueError,
)


@pytest.fixture
def option_dict():
    return {
        'auth_method': 'userpass',
        'username': None,
        'password': None,
        'mount_point': None,
    }


@pytest.fixture
def userpass_password():
    return 'opaque'


@pytest.fixture
def userpass_username():
    return 'fake-user'


@pytest.fixture
def auth_userpass(adapter, warner, deprecator):
    return HashiVaultAuthMethodUserpass(adapter, warner, deprecator)


@pytest.fixture
def userpass_login_response(fixture_loader):
    return fixture_loader('userpass_login_response.json')


class TestAuthUserpass(object):

    def test_auth_userpass_is_auth_method_base(self, auth_userpass):
        assert isinstance(auth_userpass, HashiVaultAuthMethodUserpass)
        assert issubclass(HashiVaultAuthMethodUserpass, HashiVaultAuthMethodBase)

    def test_auth_userpass_validate_direct(self, auth_userpass, adapter, userpass_username, userpass_password):
        adapter.set_option('username', userpass_username)
        adapter.set_option('password', userpass_password)

        auth_userpass.validate()

    @pytest.mark.parametrize('opt_patch', [
        {'username': 'user-only'},
        {'password': 'password-only'},
    ])
    def test_auth_userpass_validate_xfailures(self, auth_userpass, adapter, opt_patch):
        adapter.set_options(**opt_patch)

        with pytest.raises(HashiVaultValueError, match=r'Authentication method userpass requires options .*? to be set, but these are missing:'):
            auth_userpass.validate()

    @pytest.mark.parametrize('use_token', [True, False], ids=lambda x: 'use_token=%s' % x)
    @pytest.mark.parametrize('mount_point', [None, 'other'], ids=lambda x: 'mount_point=%s' % x)
    def test_auth_userpass_authenticate(
        self, auth_userpass, client, adapter, userpass_password, userpass_username, mount_point, use_token, userpass_login_response
    ):
        adapter.set_option('username', userpass_username)
        adapter.set_option('password', userpass_password)
        adapter.set_option('mount_point', mount_point)

        expected_login_params = {
            'username': userpass_username,
            'password': userpass_password,
        }
        if mount_point:
            expected_login_params['mount_point'] = mount_point

        def _set_client_token(*args, **kwargs):
            return userpass_login_response

        with mock.patch.object(client.auth.userpass, 'login', side_effect=_set_client_token) as userpass_login:
            response = auth_userpass.authenticate(client, use_token=use_token)
            userpass_login.assert_called_once_with(**expected_login_params)

        assert response['auth']['client_token'] == userpass_login_response['auth']['client_token']
        assert (client.token == userpass_login_response['auth']['client_token']) is use_token
