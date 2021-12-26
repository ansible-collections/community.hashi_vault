# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible.plugins.loader import lookup_loader
from ansible.errors import AnsibleError

from ansible_collections.community.hashi_vault.tests.unit.compat import mock

from ansible_collections.community.hashi_vault.plugins.plugin_utils._hashi_vault_lookup_base import HashiVaultLookupBase

# this "unused" import is needed for the mock.patch calls
import ansible_collections.community.hashi_vault.plugins.lookup.vault_login


@pytest.fixture
def vault_login_lookup():
    return lookup_loader.get('community.hashi_vault.vault_login')


@pytest.fixture
def mock_authenticator():
    return mock.MagicMock(validate=lambda: True, authenticate=lambda client: 'dummy')


@pytest.fixture
def minimal_vars():
    return {
        'ansible_hashi_vault_auth_method': 'token',
        'ansible_hashi_vault_url': 'http://dummy',
        'ansible_hashi_vault_token': 'dummy',
    }


class TestVaultLoginLookup(object):

    def test_vault_login_is_lookup_base(self, vault_login_lookup):
        assert issubclass(type(vault_login_lookup), HashiVaultLookupBase)

    def test_vault_login_auth_none(self, vault_login_lookup):
        with pytest.raises(AnsibleError, match=r"The 'none' auth method is not valid for this lookup"):
            vault_login_lookup.run(terms=[], variables={'ansible_hashi_vault_auth_method': 'none'})

    def test_vault_login_extra_terms(self, vault_login_lookup, mock_authenticator, minimal_vars):
        with mock.patch('ansible_collections.community.hashi_vault.plugins.lookup.vault_login.display.warning') as warning:
            with mock.patch.object(vault_login_lookup, 'authenticator', new=mock_authenticator):
                vault_login_lookup.run(terms=['', ''], variables=minimal_vars)
                warning.assert_called_once_with("Supplied term strings will be ignored. This lookup does not use term strings.")
