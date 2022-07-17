# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
from _pytest.fixtures import fixture
from _pytest.python_api import raises
__metaclass__ = type

import os
import pytest

from ansible_collections.community.hashi_vault.tests.unit.compat import mock

try:
    import hvac
except ImportError:
    # python 2.6, which isn't supported anyway
    hvac = mock.MagicMock()

from ansible_collections.community.hashi_vault.plugins.module_utils._auth_method_token import (
    HashiVaultAuthMethodToken,
)

from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import (
    HashiVaultAuthMethodBase,
    HashiVaultValueError,
)


@pytest.fixture
def option_dict():
    return {
        'auth_method': 'fake',
        'token': None,
        'token_path': None,
        'token_file': '.vault-token',
        'token_validate': True,
    }


@pytest.fixture
def token():
    return 'opaque'


@pytest.fixture
def auth_token(adapter, warner, deprecator):
    return HashiVaultAuthMethodToken(adapter, warner, deprecator)


@pytest.fixture(params=['lookup-self_with_meta.json', 'lookup-self_without_meta.json'])
def lookup_self_response(fixture_loader, request):
    return fixture_loader(request.param)


@pytest.fixture
def token_file_path(fixture_loader):
    return fixture_loader('vault-token', parse='path')


@pytest.fixture
def token_file_content(fixture_loader):
    return fixture_loader('vault-token', parse='raw').strip()


@pytest.fixture(params=[hvac.exceptions.InvalidRequest(), hvac.exceptions.Forbidden(), hvac.exceptions.InvalidPath()])
def validation_failure(request):
    return request.param


class TestAuthToken(object):

    def test_auth_token_is_auth_method_base(self, auth_token):
        assert isinstance(auth_token, HashiVaultAuthMethodToken)
        assert issubclass(HashiVaultAuthMethodToken, HashiVaultAuthMethodBase)

    def test_simulate_login_response(self, auth_token, token):
        response = auth_token._simulate_login_response(token)
        expected = {
            'auth': {
                'client_token': token
            }
        }

        assert response == expected

    def test_simulate_login_response_with_lookup(self, auth_token, token, lookup_self_response):
        response = auth_token._simulate_login_response(token, lookup_self_response)

        assert 'auth' in response
        assert response['auth']['client_token'] == token

        if 'meta' not in lookup_self_response['data']:
            return
        assert 'meta' not in response['auth']
        assert lookup_self_response['data']['meta'] == response['auth']['metadata']

    def test_auth_token_validate_direct(self, auth_token, adapter, token):
        adapter.set_option('token', token)

        auth_token.validate()

        assert adapter.get_option('token') == token

    def test_auth_token_validate_by_path(self, auth_token, adapter, token_file_path, token_file_content):
        head, tail = os.path.split(token_file_path)
        adapter.set_option('token_path', head)
        adapter.set_option('token_file', tail)

        auth_token.validate()

        assert adapter.get_option('token') == token_file_content

    @pytest.mark.parametrize('opt_patch', [
        {},
        {'token_path': '/tmp', 'token_file': '__fake_no_file'},
    ])
    def test_auth_token_validate_xfailures(self, auth_token, adapter, opt_patch):
        adapter.set_options(**opt_patch)

        with pytest.raises(HashiVaultValueError, match=r'No Vault Token specified or discovered'):
            auth_token.validate()

    def test_auth_token_file_is_directory(self, auth_token, adapter, tmp_path):
        # ensure that a token_file that exists but is a directory is treated the same as it not being found
        # see also: https://github.com/ansible-collections/community.hashi_vault/issues/152
        adapter.set_options(token_path=str(tmp_path.parent), token_file=str(tmp_path))

        with pytest.raises(HashiVaultValueError, match=r"The Vault token file '[^']+' was found but is not a file."):
            auth_token.validate()

    @pytest.mark.parametrize('use_token', [True, False], ids=lambda x: 'use_token=%s' % x)
    @pytest.mark.parametrize('lookup_self', [True, False], ids=lambda x: 'lookup_self=%s' % x)
    @pytest.mark.parametrize('token_validate', [True, False], ids=lambda x: 'token_validate=%s' % x)
    def test_auth_token_authenticate(self, auth_token, client, adapter, token, use_token, token_validate, lookup_self, lookup_self_response):
        adapter.set_option('token', token)
        adapter.set_option('token_validate', token_validate)

        expected_lookup_value = lookup_self_response if use_token and (lookup_self or token_validate) else None

        with mock.patch.object(auth_token, '_simulate_login_response', wraps=auth_token._simulate_login_response) as sim_login:
            with mock.patch.object(client.auth.token, 'lookup_self', return_value=lookup_self_response):
                response = auth_token.authenticate(client, use_token=use_token, lookup_self=lookup_self)

            sim_login.assert_called_once_with(token, expected_lookup_value)

        assert response['auth']['client_token'] == token
        assert (client.token == token) is use_token

    def test_auth_token_authenticate_success_on_no_validate(self, auth_token, adapter, client, token, validation_failure):
        adapter.set_option('token', token)
        adapter.set_option('token_validate', False)

        raiser = mock.Mock()
        raiser.side_effect = validation_failure

        with mock.patch.object(auth_token, '_simulate_login_response', wraps=auth_token._simulate_login_response) as sim_login:
            with mock.patch.object(client.auth.token, 'lookup_self', raiser):
                response = auth_token.authenticate(client, use_token=True, lookup_self=True)

            sim_login.assert_called_once_with(token, None)

        assert response['auth']['client_token'] == token
        assert client.token == token

    def test_auth_token_authenticate_failed_validation(self, auth_token, adapter, client, token, validation_failure):
        adapter.set_option('token', token)
        adapter.set_option('token_validate', True)

        raiser = mock.Mock()
        raiser.side_effect = validation_failure

        with pytest.raises(HashiVaultValueError, match=r'Invalid Vault Token Specified'):
            with mock.patch.object(client.auth.token, 'lookup_self', raiser):
                auth_token.authenticate(client, use_token=True, lookup_self=False)
