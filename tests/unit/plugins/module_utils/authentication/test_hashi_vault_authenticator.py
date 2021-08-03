# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
import pytest

from ansible_collections.community.hashi_vault.tests.unit.compat import mock

from ansible_collections.community.hashi_vault.plugins.module_utils._authenticator import HashiVaultAuthenticator


@pytest.fixture
def authenticator(fake_auth_class, adapter):
    a = HashiVaultAuthenticator(adapter, mock.MagicMock())
    a._selector = {fake_auth_class.NAME: fake_auth_class}

    return a


class TestHashiVaultAuthenticator(object):
    def test_method_validate_is_called(self, authenticator, fake_auth_class):
        authenticator.validate()

        # TODO: revisit in 2.0.0 when py3.5 is dropped
        if sys.version_info < (3, 6):
            assert fake_auth_class.validate.call_count == 1
        else:
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
