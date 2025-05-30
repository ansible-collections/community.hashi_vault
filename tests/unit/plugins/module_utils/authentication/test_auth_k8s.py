# -*- coding: utf-8 -*-
# Copyright (c) 2021 FERREIRA Christophe (@chris93111)
# Copyright (c) 2025 community.hashi_vault contributors
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible_collections.community.hashi_vault.tests.unit.compat import mock
from ansible_collections.community.hashi_vault.plugins.module_utils._auth_method_k8s import HashiVaultAuthMethodKubernetes
from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import (
    HashiVaultAuthMethodBase,
    HashiVaultValueError,
)


@pytest.fixture
def option_dict():
    return {
        'auth_method': 'kubernetes',
        'kubernetes_token': None,
        'kubernetes_token_path': '/var/run/secrets/kubernetes.io/serviceaccount/token',
        'role_id': None,
        'mount_point': None,
    }


@pytest.fixture
def kubernetes_token():
    return (
        'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJ0ZXN0Iiwic3ViIjoiaGFzaGlfdmF1bHRAdGVzdC5hbnNpYmxlLmNvbSIsIm5iZiI6MTYwND'
        'gzNTEwMCwiZXhwIjozMjQ5OTA1MTM1OX0.NEWQR_Eicw8Fa9gU9HPY2M9Rp1czNTUKrICwKe7l1edaZNtgxhMGdyqnBsPrHL_dw1ZIwdvwVAioi8bEyIDE'
        'WICls0lzHwM169rrea3WEFrB5CP17A6DkvYL0cnOnGutbwUrXInPCRUfvRogIKEI-w8X-ris9LX2FBPKhXX1K3U0D8uYi5_9t8YWywTe0NkYvY-nTzMug'
        'K1MXMoBJ3fCksweJiDp6BOo3v9OU03MLgwgri2UdsqVb7WSk4XvWG-lmbiiSAWVf9BI3mecVDUHpYxbEqjv1HDG_wdX8zy1ZlAFbjp3kIpMlDVK1Q5nu'
        '_VPDzQrEvPdTnOzU36LE4UF-w'
    )


@pytest.fixture
def role_id():
    return 'demo'


@pytest.fixture
def auth_k8s(adapter, warner, deprecator):
    return HashiVaultAuthMethodKubernetes(adapter, warner, deprecator)


@pytest.fixture
def k8s_login_response(fixture_loader):
    return fixture_loader('kubernetes_login_response.json')


class TestAuthK8s(object):

    def test_auth_k8s_is_auth_method_base(self, auth_k8s):
        assert isinstance(auth_k8s, HashiVaultAuthMethodKubernetes)
        assert issubclass(HashiVaultAuthMethodKubernetes, HashiVaultAuthMethodBase)

    def test_auth_k8s_validate_direct_token(self, auth_k8s, adapter, kubernetes_token, role_id):
        adapter.set_option('kubernetes_token', kubernetes_token)
        adapter.set_option('role_id', role_id)

        auth_k8s.validate()

    def test_auth_k8s_validate_token_from_file(self, auth_k8s, adapter, kubernetes_token, role_id):
        adapter.set_option('role_id', role_id)
        adapter.set_option('kubernetes_token_path', '/tmp/k8s_token')

        with mock.patch('os.path.exists', return_value=True):
            with mock.patch('os.path.isfile', return_value=True):
                with mock.patch('builtins.open', mock.mock_open(read_data=kubernetes_token)):
                    auth_k8s.validate()

        expected = kubernetes_token
        actual = adapter.get_option('kubernetes_token')
        assert expected == actual

    def test_auth_k8s_validate_token_file_not_found(self, auth_k8s, adapter, role_id):
        adapter.set_option('role_id', role_id)
        adapter.set_option('kubernetes_token_path', '/tmp/k8s_token')

        with mock.patch('os.path.exists', return_value=False):
            with pytest.raises(HashiVaultValueError, match='No Kubernetes Token specified or discovered'):
                auth_k8s.validate()

    def test_auth_k8s_validate_token_path_is_directory(self, auth_k8s, adapter, role_id):
        adapter.set_option('role_id', role_id)
        adapter.set_option('kubernetes_token_path', '/tmp/k8s_token')

        with mock.patch('os.path.exists', return_value=True):
            with mock.patch('os.path.isfile', return_value=False):
                with pytest.raises(HashiVaultValueError, match="was found but is not a file"):
                    auth_k8s.validate()

    def test_auth_k8s_validate_no_role_id(self, auth_k8s, adapter, kubernetes_token):
        adapter.set_option('kubernetes_token', kubernetes_token)

        with pytest.raises(HashiVaultValueError, match=r"Authentication method kubernetes requires options \('role_id',\) to be set"):
            auth_k8s.validate()

    def test_auth_k8s_validate_no_token(self, auth_k8s, adapter, role_id):
        adapter.set_option('role_id', role_id)

        with pytest.raises(HashiVaultValueError, match='No Kubernetes Token specified or discovered'):
            auth_k8s.validate()

    @pytest.mark.parametrize('use_token', [True, False])
    def test_auth_k8s_authenticate(self, auth_k8s, client, adapter, kubernetes_token, role_id, k8s_login_response, use_token):
        adapter.set_option('kubernetes_token', kubernetes_token)
        adapter.set_option('role_id', role_id)

        expected_login_params = {
            'role': role_id,
            'jwt': kubernetes_token,
            'mount_point': None,
            'use_token': use_token,
        }

        def _mock_login(role, jwt, mount_point, use_token):
            if use_token:
                client.token = k8s_login_response['auth']['client_token']
            return k8s_login_response

        with mock.patch.object(client.auth.kubernetes, 'login', side_effect=_mock_login) as k8s_login:
            response = auth_k8s.authenticate(client, use_token=use_token)

        k8s_login.assert_called_once_with(**expected_login_params)

        assert response['auth']['client_token'] == k8s_login_response['auth']['client_token']

        if use_token:
            assert client.token == k8s_login_response['auth']['client_token']

    def test_auth_k8s_authenticate_custom_mount_point(self, auth_k8s, client, adapter, kubernetes_token, role_id, k8s_login_response):
        adapter.set_option('kubernetes_token', kubernetes_token)
        adapter.set_option('role_id', role_id)
        adapter.set_option('mount_point', 'my-k8s')

        expected_login_params = {
            'role': role_id,
            'jwt': kubernetes_token,
            'mount_point': 'my-k8s',
            'use_token': True,
        }

        def _mock_login(role, jwt, mount_point, use_token):
            return k8s_login_response

        with mock.patch.object(client.auth.kubernetes, 'login', side_effect=_mock_login) as k8s_login:
            response = auth_k8s.authenticate(client)

        k8s_login.assert_called_once_with(**expected_login_params)

    def test_auth_k8s_authenticate_fallback_deprecated(self, auth_k8s, client, adapter, kubernetes_token, role_id, k8s_login_response):
        adapter.set_option('kubernetes_token', kubernetes_token)
        adapter.set_option('role_id', role_id)

        expected_login_params = {
            'role': role_id,
            'jwt': kubernetes_token,
            'mount_point': None,
            'use_token': True,
        }

        def _mock_deprecated_login(role, jwt, mount_point, use_token):
            if use_token:
                client.token = k8s_login_response['auth']['client_token']
            return k8s_login_response

        # Simulate older HVAC version without kubernetes auth support
        with mock.patch.object(client.auth.kubernetes, 'login', side_effect=NotImplementedError):
            with mock.patch.object(client, 'auth_kubernetes', create=True, side_effect=_mock_deprecated_login) as k8s_login_deprecated:
                response = auth_k8s.authenticate(client)

        k8s_login_deprecated.assert_called_once_with(**expected_login_params)

        assert response['auth']['client_token'] == k8s_login_response['auth']['client_token']
