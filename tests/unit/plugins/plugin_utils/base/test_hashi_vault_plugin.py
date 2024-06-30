# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import builtins

import pytest

from ......tests.unit.compat import mock

from ansible.plugins import AnsiblePlugin
from ansible.errors import AnsibleError

from ansible_collections.community.hashi_vault.plugins.plugin_utils._hashi_vault_plugin import HashiVaultPlugin
from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import HashiVaultOptionAdapter


@pytest.fixture
def hashi_vault_plugin():
    return HashiVaultPlugin()


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


class TestHashiVaultPlugin(object):

    def test_is_ansible_plugin(self, hashi_vault_plugin):
        assert issubclass(type(hashi_vault_plugin), AnsiblePlugin)

    def test_has_option_adapter(self, hashi_vault_plugin):
        assert hasattr(hashi_vault_plugin, '_options_adapter') and issubclass(type(hashi_vault_plugin._options_adapter), HashiVaultOptionAdapter)

    def test_raises_ansible_error_when_hvac_missing(self, hvac_fail_import_hook):
        with pytest.raises(AnsibleError) as hvac_import:
            HashiVaultPlugin()
        assert hvac_import.value._message.startswith("Failed to import the required Python library (hvac) on")

    # TODO: remove when deprecate() is no longer needed
    def test_has_process_deprecations(self, hashi_vault_plugin):
        assert hasattr(hashi_vault_plugin, 'process_deprecations') and callable(hashi_vault_plugin.process_deprecations)
