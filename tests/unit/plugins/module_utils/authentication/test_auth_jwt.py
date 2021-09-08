# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible_collections.community.hashi_vault.tests.unit.compat import mock

from ansible_collections.community.hashi_vault.plugins.module_utils._auth_method_jwt import (
    HashiVaultAuthMethodJwt,
)

from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import (
    HashiVaultAuthMethodBase,
    HashiVaultValueError,
)


@pytest.fixture
def option_dict():
    return {
        'auth_method': 'jwt',
        'jwt': None,
        'role_id': None,
        'mount_point': None,
    }


@pytest.fixture
def jwt():
    return 'opaque'


@pytest.fixture
def role_id():
    return 'fake-role'


@pytest.fixture
def auth_jwt(adapter, warner):
    return HashiVaultAuthMethodJwt(adapter, warner)


@pytest.fixture
def jwt_login_response(fixture_loader):
    return fixture_loader('jwt_login_response.json')


class TestAuthJwt(object):

    def test_auth_jwt_is_auth_method_base(self, auth_jwt):
        assert isinstance(auth_jwt, HashiVaultAuthMethodJwt)
        assert issubclass(HashiVaultAuthMethodJwt, HashiVaultAuthMethodBase)

    def test_auth_jwt_validate_direct(self, auth_jwt, adapter, jwt, role_id):
        adapter.set_option('jwt', jwt)
        adapter.set_option('role_id', role_id)

        auth_jwt.validate()

    @pytest.mark.parametrize('opt_patch', [
        {},
        {'role_id': 'role_id-only'},
        {'jwt': 'jwt-only'}
    ])
    def test_auth_jwt_validate_xfailures(self, auth_jwt, adapter, opt_patch):
        adapter.set_options(**opt_patch)

        with pytest.raises(HashiVaultValueError, match=r'Authentication method jwt requires options .*? to be set, but these are missing:'):
            auth_jwt.validate()

    @pytest.mark.parametrize('use_token', [True, False], ids=lambda x: 'use_token=%s' % x)
    @pytest.mark.parametrize('mount_point', [None, 'other'], ids=lambda x: 'mount_point=%s' % x)
    def test_auth_jwt_authenticate(self, auth_jwt, client, adapter, jwt, role_id, mount_point, use_token, jwt_login_response):
        adapter.set_option('jwt', jwt)
        adapter.set_option('role_id', role_id)
        adapter.set_option('mount_point', mount_point)

        expected_login_params = {
            'jwt': jwt,
            'role': role_id,
        }
        if mount_point:
            expected_login_params['path'] = mount_point

        with mock.patch.object(client.auth.jwt, 'jwt_login', return_value=jwt_login_response) as jwt_login:
            response = auth_jwt.authenticate(client, use_token=use_token)
            jwt_login.assert_called_once_with(**expected_login_params)

        assert response['auth']['client_token'] == jwt_login_response['auth']['client_token']
        assert (client.token == jwt_login_response['auth']['client_token']) is use_token
