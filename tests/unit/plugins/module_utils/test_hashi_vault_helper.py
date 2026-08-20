# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import builtins
import os
import pytest
import sys

from .....tests.unit.compat import mock
from .....plugins.module_utils._hashi_vault_common import (
    HashiVaultHVACError,
    HashiVaultHelper,
)


@pytest.fixture
def hashi_vault_helper():
    return HashiVaultHelper()


@pytest.fixture
def hashi_vault_hvac_error():
    return HashiVaultHVACError(error='test error', msg='message')


@pytest.fixture
def hvac_fail_import_hook():
    original_import = builtins.__import__

    def _mock(name: str, *args, **kwargs):
        if name == 'hvac':
            raise ImportError('test case module import failure')

        return original_import(name, *args, **kwargs)

    with mock.patch.object(builtins, '__import__', _mock):
        yield

    builtins.__import__ = original_import


@pytest.fixture
def hvac_success_import_hook():
    original_import = sys.modules['hvac']
    sys.modules['hvac'] = mock.Mock()
    yield

    sys.modules['hvac'] = original_import


@pytest.fixture
def vault_token():
    return 'fake123'


@pytest.fixture
def vault_token_via_env(vault_token):
    with mock.patch.dict(os.environ, {'VAULT_TOKEN': vault_token}):
        yield


class TestHashiVaultHelper(object):

    def test_create_base_error(self, hashi_vault_hvac_error):
        hvac_error = hashi_vault_hvac_error

        assert isinstance(hvac_error, (HashiVaultHVACError, ImportError))
        assert hasattr(hvac_error, 'error')
        assert hasattr(hvac_error, 'msg')

    def test_hashi_vault_helper_fails_when_hvac_not_available(self, hvac_fail_import_hook):
        with pytest.raises(HashiVaultHVACError) as hvac_import:
            HashiVaultHelper()
        assert hvac_import.value.error == "test case module import failure"

    def test_hashi_vault_helper_uses_loaded_hvac(self, hvac_success_import_hook):
        client = HashiVaultHelper()
        assert hasattr(client, 'hvac')

    def test_get_vault_client_without_logout_explicit_token(self, hashi_vault_helper, vault_token):
        client = hashi_vault_helper.get_vault_client(token=vault_token)

        assert client.token == vault_token

    def test_get_vault_client_without_logout_implicit_token(self, hashi_vault_helper, vault_token, vault_token_via_env):
        client = hashi_vault_helper.get_vault_client(hashi_vault_logout_inferred_token=False)

        assert client.token == vault_token

    def test_get_vault_client_with_logout_implicit_token(self, hashi_vault_helper, vault_token_via_env):
        client = hashi_vault_helper.get_vault_client(hashi_vault_logout_inferred_token=True)

        assert client.token is None
