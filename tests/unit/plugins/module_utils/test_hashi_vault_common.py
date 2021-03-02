# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
import os
import pytest

from ansible_collections.community.hashi_vault.tests.unit.compat import mock
from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import HashiVaultHelper


@pytest.fixture
def hashi_vault_helper():
    return HashiVaultHelper()


@pytest.fixture
def vault_token():
    return 'fake123'


@pytest.fixture
def vault_token_via_env(vault_token):
    with mock.patch.dict(os.environ, {'VAULT_TOKEN': vault_token}):
        yield


@pytest.mark.skipif(sys.version_info < (2, 7), reason="Python 2.7 or higher is required.")
class TestHashiVaultHelper(object):

    def test_get_vault_client_without_logout_explicit_token(self, hashi_vault_helper, vault_token):
        client = hashi_vault_helper.get_vault_client(token=vault_token)

        assert client.token == vault_token

    def test_get_vault_client_without_logout_implicit_token(self, hashi_vault_helper, vault_token, vault_token_via_env):
        client = hashi_vault_helper.get_vault_client(hashi_vault_logout_inferred_token=False)

        assert client.token == vault_token

    def test_get_vault_client_with_logout_implicit_token(self, hashi_vault_helper, vault_token_via_env):
        client = hashi_vault_helper.get_vault_client(hashi_vault_logout_inferred_token=True)

        assert client.token is None
