# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible_collections.community.hashi_vault.tests.unit.compat import mock

from ansible_collections.community.hashi_vault.plugins.module_utils._authenticator import HashiVaultAuthenticator


@pytest.fixture
def authenticator(fake_auth_class, adapter, warner, deprecator):
    a = HashiVaultAuthenticator(adapter, warner, deprecator)
    a._selector.update({fake_auth_class.NAME: fake_auth_class})

    return a


class TestHashiVaultAuthenticator(object):
    def test_method_validate_is_called(self, authenticator, fake_auth_class):
        authenticator.validate()

        fake_auth_class.validate.assert_called_once()

    def test_validate_not_implemented(self, authenticator, fake_auth_class):
        with pytest.raises(NotImplementedError):
            authenticator.validate(method='missing')

        fake_auth_class.validate.assert_not_called()

    @pytest.mark.parametrize('args', [
        [],
        ['one'],
        ['one', 2, 'three'],
    ])
    @pytest.mark.parametrize('kwargs', [
        {},
        {'one': 1},
        {'one': '1', 'two': 2},
    ])
    def test_method_authenticate_is_called(self, authenticator, fake_auth_class, args, kwargs):
        authenticator.authenticate(*args, **kwargs)

        fake_auth_class.authenticate.assert_called_once_with(*args, **kwargs)

    def test_authenticate_not_implemented(self, authenticator, fake_auth_class):
        with pytest.raises(NotImplementedError):
            authenticator.validate(method='missing')

        fake_auth_class.authenticate.assert_not_called()

    def test_get_method_object_explicit(self, authenticator):
        for auth_method, obj in authenticator._selector.items():
            assert authenticator._get_method_object(method=auth_method) == obj

    def test_get_method_object_missing(self, authenticator):
        with pytest.raises(NotImplementedError, match=r"auth method 'missing' is not implemented in HashiVaultAuthenticator"):
            authenticator._get_method_object(method='missing')

    def test_get_method_object_implicit(self, authenticator, adapter, fake_auth_class):
        adapter.set_option('auth_method', fake_auth_class.NAME)

        obj = authenticator._get_method_object()

        assert isinstance(obj, type(fake_auth_class))

    @pytest.mark.parametrize('revoke', [True, False])
    def test_method_logout_logs_out_with_token_if_revocation_requested(self, authenticator, fake_auth_class, adapter, revoke):
        adapter.set_option("revoke_ephemeral_token", revoke)
        client = mock.MagicMock()

        authenticator.logout(client)

        client.logout.assert_called_once_with(revoke_token=revoke)

    def test_logout_not_implemented(self, authenticator, fake_auth_class):
        client = mock.MagicMock()

        with pytest.raises(NotImplementedError):
            authenticator.logout(client, method='missing')

        fake_auth_class.should_revoke_token.assert_not_called()
