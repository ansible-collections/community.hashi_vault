# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible_collections.community.hashi_vault.tests.unit.compat import mock

from ansible_collections.community.hashi_vault.plugins.module_utils._authenticator import HashiVaultAuthenticator


@pytest.fixture
def mock_warner():
    return mock.MagicMock()


@pytest.fixture
def authenticator(fake_auth_class, adapter, mock_warner):
    a = HashiVaultAuthenticator(adapter, mock_warner)
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

    # TODO: remove in 3.0.0 when aws_iam_login name is removed
    # https://github.com/ansible-collections/community.hashi_vault/pull/193
    def test_get_method_object_deprecated_aws_iam_login(self, authenticator, mock_warner):
        obj = authenticator._get_method_object('aws_iam_login')

        assert obj == authenticator._selector['aws_iam']
        mock_warner.assert_called_once_with(
            "[DEPRECATION WARNING]: auth method 'aws_iam_login' is renamed to 'aws_iam'. "
            "The 'aws_iam_login' name will be removed in community.hashi_vault 3.0.0."
        )
