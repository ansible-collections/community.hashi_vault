from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

# from ansible_collections.community.hashi_vault.tests.unit.compat import unittest
# from ansible_collections.community.hashi_vault.tests.unit.compat.mock import patch, MagicMock

from ansible_collections.community.hashi_vault.plugins.lookup.hashi_vault import LookupModule  # , HashiVault
from ansible_collections.community.hashi_vault.plugins.lookup.__init__ import HashiVaultLookupBase


@pytest.fixture
def hashi_vault_lookup_module():
    return LookupModule()


class TestHashiVaultLookup(object):

    def test_is_hashi_vault_lookup_base(self, hashi_vault_lookup_module):
        assert issubclass(type(hashi_vault_lookup_module), HashiVaultLookupBase)
