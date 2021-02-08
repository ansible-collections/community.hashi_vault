# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible_collections.community.hashi_vault.plugins.lookup.hashi_vault import LookupModule  # , HashiVault
from ansible_collections.community.hashi_vault.plugins.lookup.__init__ import HashiVaultLookupBase


@pytest.fixture
def hashi_vault_lookup_module():
    return LookupModule()


class TestHashiVaultLookup(object):

    def test_is_hashi_vault_lookup_base(self, hashi_vault_lookup_module):
        assert issubclass(type(hashi_vault_lookup_module), HashiVaultLookupBase)
