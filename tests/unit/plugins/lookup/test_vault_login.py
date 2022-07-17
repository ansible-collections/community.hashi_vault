# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible.plugins.loader import lookup_loader
from ansible.errors import AnsibleError

from ansible_collections.community.hashi_vault.tests.unit.compat import mock

from ansible_collections.community.hashi_vault.plugins.plugin_utils._hashi_vault_lookup_base import HashiVaultLookupBase

from .....plugins.lookup import vault_login


pytest.importorskip('hvac')


pytestmark = pytest.mark.usefixtures(
    'patch_authenticator',
    'patch_get_vault_client',
)


@pytest.fixture
def vault_login_lookup():
    return lookup_loader.get('community.hashi_vault.vault_login')


class TestVaultLoginLookup(object):

    def test_vault_login_is_lookup_base(self, vault_login_lookup):
        assert issubclass(type(vault_login_lookup), HashiVaultLookupBase)

    def test_vault_login_no_hvac(self, vault_login_lookup, minimal_vars):
        with mock.patch.object(vault_login, 'HVAC_IMPORT_ERROR', new=ImportError()):
            with pytest.raises(AnsibleError, match=r"This plugin requires the 'hvac' Python library"):
                vault_login_lookup.run(terms='fake', variables=minimal_vars)

    def test_vault_login_auth_none(self, vault_login_lookup):
        with pytest.raises(AnsibleError, match=r"The 'none' auth method is not valid for this lookup"):
            vault_login_lookup.run(terms=[], variables={'ansible_hashi_vault_auth_method': 'none'})

    def test_vault_login_extra_terms(self, vault_login_lookup, authenticator, minimal_vars):
        with mock.patch('ansible_collections.community.hashi_vault.plugins.lookup.vault_login.display.warning') as warning:
            with mock.patch.object(vault_login_lookup, 'authenticator', new=authenticator):
                vault_login_lookup.run(terms=['', ''], variables=minimal_vars)
                warning.assert_called_once_with("Supplied term strings will be ignored. This lookup does not use term strings.")
