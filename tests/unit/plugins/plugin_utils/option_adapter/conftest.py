# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

# this file must define the "adapter" fixture at a minimum,
# and anything else that it needs or depends on that isn't already defined in in the test files themselves.

# Keep in mind that this one is for plugin_utils and so it can depend on
# or import controller-side code, however it will only be run against python versions
# that are supported on the controller.

import pytest

from ansible.plugins import AnsiblePlugin

from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import HashiVaultOptionAdapter


class FakePlugin(AnsiblePlugin):
    _load_name = 'community.hashi_vault.fake'


@pytest.fixture
def ansible_plugin(sample_dict):
    plugin = FakePlugin()
    plugin._options = sample_dict
    return plugin


@pytest.fixture
def adapter_from_ansible_plugin(ansible_plugin):
    def _create_adapter_from_ansible_plugin():
        return HashiVaultOptionAdapter.from_ansible_plugin(ansible_plugin)

    return _create_adapter_from_ansible_plugin


@pytest.fixture(params=['dict', 'dict_defaults', 'ansible_plugin'])
def adapter(request, adapter_from_dict, adapter_from_dict_defaults, adapter_from_ansible_plugin):
    return {
        'dict': adapter_from_dict,
        'dict_defaults': adapter_from_dict_defaults,
        'ansible_plugin': adapter_from_ansible_plugin,
    }[request.param]()
