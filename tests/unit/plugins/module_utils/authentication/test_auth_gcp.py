# -*- coding: utf-8 -*-
# Copyright (c) 2024 Michael Woodham (woodham@google.com)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible_collections.community.hashi_vault.tests.unit.compat import mock

from ansible_collections.community.hashi_vault.plugins.module_utils._auth_method_gcp import (
    HashiVaultAuthMethodGcp,
)

from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import (
    HashiVaultAuthMethodBase,
    HashiVaultValueError,
)


@pytest.fixture
def option_dict():
    return {
        'auth_method': 'gcp',
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
def auth_gcp(adapter, warner, deprecator):
    return HashiVaultAuthMethodGcp(adapter, warner, deprecator)


@pytest.fixture
def gcp_login_response(fixture_loader):
    return fixture_loader('gcp_login_response.json')


class TestAuthGcp(object):

    def test_auth_gcp_is_auth_method_base(self, auth_gcp):
        assert isinstance(auth_gcp, HashiVaultAuthMethodGcp)
        assert issubclass(HashiVaultAuthMethodGcp, HashiVaultAuthMethodBase)

    def test_auth_gcp_validate_role_id(self, auth_gcp, adapter):
        adapter.set_options(role_id=None)
        with pytest.raises(HashiVaultValueError, match=r'^Authentication method gcp requires options .*? to be set, but these are missing:'):
            auth_gcp.validate()

    def test_auth_gcp_validate_direct(self, auth_gcp, adapter, jwt, role_id):
        adapter.set_option('jwt', jwt)
        adapter.set_option('role_id', role_id)

        auth_gcp.validate()

    @pytest.mark.parametrize('opt_patch', [
        {},
        {'role_id': 'my-role'},
        {'jwt': 'jwt-only'}
    ])
    def test_auth_jwt_validate_xfailures(self, auth_gcp, adapter, opt_patch):
        adapter.set_options(**opt_patch)

        with pytest.raises(HashiVaultValueError, match=r'Authentication method gcp requires options .*? to be set, but these are missing:'):
            auth_gcp.validate()

    @pytest.mark.parametrize('use_token', [True, False], ids=lambda x: 'use_token=%s' % x)
    @pytest.mark.parametrize('mount_point', [None, 'other'], ids=lambda x: 'mount_point=%s' % x)
    def test_auth_gcp_authenticate(self, auth_gcp, client, adapter, jwt, role_id, mount_point, use_token, gcp_login_response):
        adapter.set_option('jwt', jwt)
        adapter.set_option('role_id', role_id)
        adapter.set_option('mount_point', mount_point)

        auth_gcp.validate()

        expected_login_params = {
            'jwt': jwt,
            'role': role_id,
        }

        if mount_point:
            expected_login_params['mount_point'] = mount_point

        with mock.patch.object(client.auth.gcp, 'login', return_value=gcp_login_response) as gcp_login:
            response = auth_gcp.authenticate(client, use_token=use_token)
            gcp_login.assert_called_once_with(**expected_login_params, use_token=mock.ANY)

        assert response['auth']['client_token'] == gcp_login_response['auth']['client_token']
        assert (client.token == gcp_login_response['auth']['client_token']) is use_token
