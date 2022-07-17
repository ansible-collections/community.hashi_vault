# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible_collections.community.hashi_vault.tests.unit.compat import mock

from ansible_collections.community.hashi_vault.plugins.module_utils._auth_method_ldap import (
    HashiVaultAuthMethodLdap,
)

from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import (
    HashiVaultAuthMethodBase,
    HashiVaultValueError,
)


@pytest.fixture
def option_dict():
    return {
        'auth_method': 'ldap',
        'username': None,
        'password': None,
        'mount_point': None,
    }


@pytest.fixture
def ldap_username():
    return 'ldapuser'


@pytest.fixture
def ldap_password():
    return 's3cret'


@pytest.fixture
def auth_ldap(adapter, warner, deprecator):
    return HashiVaultAuthMethodLdap(adapter, warner, deprecator)


@pytest.fixture
def ldap_login_response(fixture_loader):
    return fixture_loader('ldap_login_response.json')


class TestAuthLdap(object):

    def test_auth_ldap_is_auth_method_base(self, auth_ldap):
        assert isinstance(auth_ldap, HashiVaultAuthMethodLdap)
        assert issubclass(HashiVaultAuthMethodLdap, HashiVaultAuthMethodBase)

    @pytest.mark.parametrize('mount_point', [None, 'other'], ids=lambda x: 'mount_point=%s' % x)
    def test_auth_ldap_validate(self, auth_ldap, adapter, ldap_username, ldap_password, mount_point):
        adapter.set_options(username=ldap_username, password=ldap_password, mount_point=mount_point)

        auth_ldap.validate()

    @pytest.mark.parametrize('opt_patch', [
        {'username': 'user-only'},
        {'password': 'password-only'},
    ])
    def test_auth_ldap_validate_xfailures(self, auth_ldap, adapter, opt_patch):
        adapter.set_options(**opt_patch)

        with pytest.raises(HashiVaultValueError, match=r'Authentication method ldap requires options .*? to be set, but these are missing:'):
            auth_ldap.validate()

    @pytest.mark.parametrize('use_token', [True, False], ids=lambda x: 'use_token=%s' % x)
    @pytest.mark.parametrize('mount_point', [None, 'other'], ids=lambda x: 'mount_point=%s' % x)
    def test_auth_ldap_authenticate(
        self, auth_ldap, client, adapter, ldap_password, ldap_username, mount_point, use_token, ldap_login_response
    ):
        adapter.set_option('username', ldap_username)
        adapter.set_option('password', ldap_password)
        adapter.set_option('mount_point', mount_point)

        expected_login_params = {
            'username': ldap_username,
            'password': ldap_password,
        }
        if mount_point:
            expected_login_params['mount_point'] = mount_point

        auth_ldap.validate()

        def _set_client_token(*args, **kwargs):
            if kwargs['use_token']:
                client.token = ldap_login_response['auth']['client_token']
            return ldap_login_response

        with mock.patch.object(client.auth.ldap, 'login', side_effect=_set_client_token) as ldap_login:
            response = auth_ldap.authenticate(client, use_token=use_token)
            ldap_login.assert_called_once_with(use_token=use_token, **expected_login_params)

        assert response['auth']['client_token'] == ldap_login_response['auth']['client_token']
        assert (client.token == ldap_login_response['auth']['client_token']) is use_token
