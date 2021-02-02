from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible.plugins.lookup import LookupBase

from ansible_collections.community.hashi_vault.plugins.plugin_utils.hashi_vault_plugin import HashiVaultPlugin
from ansible_collections.community.hashi_vault.plugins.lookup.__init__ import HashiVaultLookupBase


@pytest.fixture
def hashi_vault_lookup_module():
    return FakeLookupModule()


class FakeLookupModule(HashiVaultLookupBase):
    def run(self, terms, variables=None, **kwargs):
        pass


class TestHashiVaultLookupBase(object):

    def test_is_hashi_vault_plugin(self, hashi_vault_lookup_module):
        assert issubclass(type(hashi_vault_lookup_module), HashiVaultPlugin)

    def test_is_ansible_lookup_base(self, hashi_vault_lookup_module):
        assert issubclass(type(hashi_vault_lookup_module), LookupBase)
