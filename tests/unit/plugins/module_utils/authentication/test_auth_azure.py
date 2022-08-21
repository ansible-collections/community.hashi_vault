# -*- coding: utf-8 -*-
# Copyright (c) 2022 Junrui Chen (@jchenship)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible_collections.community.hashi_vault.tests.unit.compat import mock

from ansible_collections.community.hashi_vault.plugins.module_utils._auth_method_azure import (
    HashiVaultAuthMethodAzure,
)

from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import (
    HashiVaultAuthMethodBase,
    HashiVaultValueError,
)


@pytest.fixture
def option_dict():
    return {
        'auth_method': 'azure',
        'role_id': 'vault-role',
        'mount_point': None,
        'jwt': None,
        'azure_tenant_id': None,
        'azure_client_id': None,
        'azure_client_secret': None,
        'azure_resource': 'https://management.azure.com/',
    }


@pytest.fixture
def azure_client_id():
    return 'client-id'


@pytest.fixture
def azure_client_secret():
    return 'client-secret'


@pytest.fixture
def jwt():
    return 'jwt-token'


@pytest.fixture
def auth_azure(adapter, warner, deprecator):
    return HashiVaultAuthMethodAzure(adapter, warner, deprecator)


@pytest.fixture
def azure_login_response(fixture_loader):
    return fixture_loader('azure_login_response.json')


class TestAuthAzure(object):
    def test_auth_azure_is_auth_method_base(self, auth_azure):
        assert isinstance(auth_azure, HashiVaultAuthMethodAzure)
        assert issubclass(HashiVaultAuthMethodAzure, HashiVaultAuthMethodBase)

    def test_auth_azure_validate_role_id(self, auth_azure, adapter):
        adapter.set_options(role_id=None)
        with pytest.raises(HashiVaultValueError, match=r'^role_id is required for azure authentication\.$'):
            auth_azure.validate()

    @pytest.mark.parametrize('mount_point', [None, 'other'], ids=lambda x: 'mount_point=%s' % x)
    @pytest.mark.parametrize('role_id', ['role1', 'role2'], ids=lambda x: 'role_id=%s' % x)
    @pytest.mark.parametrize('jwt', ['jwt1', 'jwt2'], ids=lambda x: 'jwt=%s' % x)
    def test_auth_azure_validate_use_jwt(
        self, auth_azure, adapter, role_id, mount_point, jwt
    ):
        adapter.set_options(
            role_id=role_id,
            mount_point=mount_point,
            jwt=jwt,
        )

        auth_azure.validate()

        params = auth_azure._auth_azure_login_params

        assert (mount_point is None and 'mount_point' not in params) or params['mount_point'] == mount_point
        assert params['role'] == role_id
        assert params['jwt'] == jwt

    @pytest.mark.parametrize('mount_point', [None, 'other'], ids=lambda x: 'mount_point=%s' % x)
    @pytest.mark.parametrize('use_token', [True, False], ids=lambda x: 'use_token=%s' % x)
    def test_auth_azure_authenticate_use_jwt(
        self,
        auth_azure,
        client,
        adapter,
        mount_point,
        jwt,
        use_token,
        azure_login_response,
    ):
        adapter.set_options(
            mount_point=mount_point,
            jwt=jwt,
        )

        auth_azure.validate()

        params = auth_azure._auth_azure_login_params.copy()

        with mock.patch.object(
            client.auth.azure, 'login', return_value=azure_login_response
        ) as azure_login:
            response = auth_azure.authenticate(client, use_token=use_token)
            azure_login.assert_called_once_with(use_token=use_token, **params)

        assert (
            response['auth']['client_token']
            == azure_login_response['auth']['client_token']
        )

    def test_auth_azure_validate_use_identity_no_azure_identity_lib(
        self, auth_azure, mock_import_error, adapter
    ):
        adapter.set_options()
        with mock_import_error('azure.identity'):
            with pytest.raises(
                HashiVaultValueError, match=r'azure-identity is required'
            ):
                auth_azure.validate()

    @pytest.mark.parametrize('azure_tenant_id', ['tenant1', 'tenant2'], ids=lambda x: 'azure_tenant_id=%s' % x)
    @pytest.mark.parametrize('azure_client_id', ['client1', 'client2'], ids=lambda x: 'azure_client_id=%s' % x)
    @pytest.mark.parametrize('azure_client_secret', ['secret1', 'secret2'], ids=lambda x: 'azure_client_secret=%s' % x)
    @pytest.mark.parametrize('jwt', ['jwt1', 'jwt2'], ids=lambda x: 'jwt=%s' % x)
    def test_auth_azure_validate_use_service_principal(
        self,
        auth_azure,
        adapter,
        jwt,
        azure_tenant_id,
        azure_client_id,
        azure_client_secret,
    ):
        adapter.set_options(
            azure_tenant_id=azure_tenant_id,
            azure_client_id=azure_client_id,
            azure_client_secret=azure_client_secret,
        )

        with mock.patch(
            'azure.identity.ClientSecretCredential'
        ) as mocked_credential_class:
            credential = mocked_credential_class.return_value
            credential.get_token.return_value.token = jwt
            auth_azure.validate()

            assert mocked_credential_class.called_once_with(
                azure_tenant_id, azure_client_id, azure_client_secret
            )
            assert credential.get_token.called_once_with(
                'https://management.azure.com//.default'
            )

        params = auth_azure._auth_azure_login_params
        assert params['jwt'] == jwt

    def test_auth_azure_validate_use_service_principal_no_tenant_id(
        self, auth_azure, adapter, azure_client_id, azure_client_secret
    ):
        adapter.set_options(
            azure_client_id=azure_client_id,
            azure_client_secret=azure_client_secret,
        )

        with pytest.raises(HashiVaultValueError, match='azure_tenant_id is required'):
            auth_azure.validate()

    @pytest.mark.parametrize('azure_client_id', ['client1', 'client2'], ids=lambda x: 'azure_client_id=%s' % x)
    @pytest.mark.parametrize('jwt', ['jwt1', 'jwt2'], ids=lambda x: 'jwt=%s' % x)
    def test_auth_azure_validate_use_user_managed_identity(
        self, auth_azure, adapter, jwt, azure_client_id
    ):
        adapter.set_options(
            azure_client_id=azure_client_id,
        )

        with mock.patch(
            'azure.identity.ManagedIdentityCredential'
        ) as mocked_credential_class:
            credential = mocked_credential_class.return_value
            credential.get_token.return_value.token = jwt
            auth_azure.validate()

            assert mocked_credential_class.called_once_with(azure_client_id)
            assert credential.get_token.called_once_with(
                'https://management.azure.com//.default'
            )

        params = auth_azure._auth_azure_login_params
        assert params['jwt'] == jwt

    @pytest.mark.parametrize('jwt', ['jwt1', 'jwt2'], ids=lambda x: 'jwt=%s' % x)
    def test_auth_azure_validate_use_system_managed_identity(
        self, auth_azure, adapter, jwt
    ):
        adapter.set_options()

        with mock.patch(
            'azure.identity.ManagedIdentityCredential'
        ) as mocked_credential_class:
            credential = mocked_credential_class.return_value
            credential.get_token.return_value.token = jwt
            auth_azure.validate()

            assert mocked_credential_class.called_once_with()
            assert credential.get_token.called_once_with(
                'https://management.azure.com//.default'
            )

        params = auth_azure._auth_azure_login_params
        assert params['jwt'] == jwt
