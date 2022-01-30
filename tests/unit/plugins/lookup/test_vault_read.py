# -*- coding: utf-8 -*-
# Copyright (c) 2022 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible.plugins.loader import lookup_loader

from ansible_collections.community.hashi_vault.plugins.plugin_utils._hashi_vault_lookup_base import HashiVaultLookupBase


@pytest.fixture
def vault_read_lookup():
    return lookup_loader.get('community.hashi_vault.vault_read')


class TestVaultReadLookup(object):

    def test_vault_read_is_lookup_base(self, vault_read_lookup):
        assert issubclass(type(vault_read_lookup), HashiVaultLookupBase)
