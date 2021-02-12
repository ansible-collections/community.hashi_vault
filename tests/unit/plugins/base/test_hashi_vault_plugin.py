# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible.plugins import AnsiblePlugin

from ansible_collections.community.hashi_vault.plugins.plugin_utils.hashi_vault_plugin import HashiVaultPlugin


@pytest.fixture
def hashi_vault_plugin():
    return HashiVaultPlugin()


class TestHashiVaultPlugin(object):

    def test_is_ansible_plugin(self, hashi_vault_plugin):
        assert issubclass(type(hashi_vault_plugin), AnsiblePlugin)

    # TODO: remove when deprecate() is no longer needed
    def test_has_process_deprecations(self, hashi_vault_plugin):
        assert hasattr(hashi_vault_plugin, 'process_deprecations') and callable(hashi_vault_plugin.process_deprecations)
