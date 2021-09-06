# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible_collections.community.hashi_vault.tests.unit.compat import mock

from ansible_collections.community.hashi_vault.plugins.module_utils._auth_method_approle import (
    HashiVaultAuthMethodApprole,
)

from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import (
    HashiVaultAuthMethodBase,
    HashiVaultValueError,
)


@pytest.fixture
def option_dict():
    return {
        'auth_method': 'approle',
        'secret_id': None,
        'role_id': None,
        'mount_point': None,
    }


@pytest.fixture
def secret_id():
    return 'opaque'


@pytest.fixture
def role_id():
    return 'fake-role'


@pytest.fixture
def auth_approle(adapter, warner):
    return HashiVaultAuthMethodApprole(adapter, warner)


@pytest.fixture
def approle_login_response(fixture_loader):
    return fixture_loader('approle_login_response.json')


class TestAuthApprole(object):

    def test_auth_approle_is_auth_method_base(self, auth_approle):
        assert isinstance(auth_approle, HashiVaultAuthMethodApprole)
        assert issubclass(HashiVaultAuthMethodApprole, HashiVaultAuthMethodBase)

    def test_auth_approle_validate_direct(self, auth_approle, adapter, role_id):
        adapter.set_option('role_id', role_id)

        auth_approle.validate()

    @pytest.mark.parametrize('opt_patch', [
        {},
        {'secret_id': 'secret_id-only'},
    ])
    def test_auth_approle_validate_xfailures(self, auth_approle, adapter, opt_patch):
        adapter.set_options(**opt_patch)

        with pytest.raises(HashiVaultValueError, match=r'Authentication method approle requires options .*? to be set, but these are missing:'):
            auth_approle.validate()

    @pytest.mark.parametrize('use_token', [True, False], ids=lambda x: 'use_token=%s' % x)
    @pytest.mark.parametrize('mount_point', [None, 'other'], ids=lambda x: 'mount_point=%s' % x)
    def test_auth_approle_authenticate(self, auth_approle, client, adapter, secret_id, role_id, mount_point, use_token, approle_login_response):
        adapter.set_option('secret_id', secret_id)
        adapter.set_option('role_id', role_id)
        adapter.set_option('mount_point', mount_point)

        expected_login_params = {
            'secret_id': secret_id,
            'role_id': role_id,
            'use_token': use_token,
        }
        if mount_point:
            expected_login_params['mount_point'] = mount_point

        def _set_client_token(*args, **kwargs):
            if kwargs['use_token']:
                client.token = approle_login_response['auth']['client_token']
            return approle_login_response

        with mock.patch.object(client.auth.approle, 'login', side_effect=_set_client_token) as approle_login:
            response = auth_approle.authenticate(client, use_token=use_token)
            approle_login.assert_called_once_with(**expected_login_params)

        assert response['auth']['client_token'] == approle_login_response['auth']['client_token']
        assert (client.token == approle_login_response['auth']['client_token']) is use_token
