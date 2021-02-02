from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

# from ansible_collections.community.hashi_vault.tests.unit.compat import unittest
# from ansible_collections.community.hashi_vault.tests.unit.compat.mock import patch

from ansible.plugins import AnsiblePlugin

from ansible_collections.community.hashi_vault.plugins.plugin_utils.hashi_vault_plugin import HashiVaultPlugin


@pytest.fixture
def hashi_vault_plugin():
    return HashiVaultPlugin()


class TestHashiVaultPlugin(object):

    def test_is_ansible_plugin(self, hashi_vault_plugin):
        assert issubclass(type(hashi_vault_plugin), AnsiblePlugin)

    # TODO: remove when deprecate() is no longer needed
    def test_has_deprecate(self, hashi_vault_plugin):
        assert hasattr(hashi_vault_plugin, 'deprecate') and callable(hashi_vault_plugin.deprecate)
