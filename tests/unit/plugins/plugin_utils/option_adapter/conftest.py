# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

# this file must define the "adapter" fixture at a minimum,
# and anything else that it needs or depends on that isn't already defined in in the test files themselves.

# Keep in mind that this one is for plugin_utils and so it can depend on
# or import controller-side code, however it will only be run against python versions
# that are supported on the controller.

import pytest

from packaging import version
from ansible.release import __version__ as ansible_version
from ansible.plugins import AnsiblePlugin

from ......plugins.module_utils._hashi_vault_common import HashiVaultOptionAdapter


ver = version.parse(ansible_version)
cutoff = version.parse('2.17')
option_adapter_from_plugin_marks = pytest.mark.option_adapter_raise_on_missing if ver.release >= cutoff.release else []
# https://github.com/ansible-collections/community.hashi_vault/issues/417


def _generate_options(opts: dict) -> dict:
    return {k: {"type": type(v).__name__} if v is not None else {} for k, v in opts.items()}


@pytest.fixture
def ansible_plugin(sample_dict):
    optdef = _generate_options(opts=sample_dict)

    class LookupModule(AnsiblePlugin):
        _load_name = 'community.hashi_vault.fake'

    import ansible.constants as C
    C.config.initialize_plugin_configuration_definitions("lookup", LookupModule._load_name, optdef)
    plugin = LookupModule()
    plugin._options = sample_dict
    return plugin


@pytest.fixture
def adapter_from_ansible_plugin(ansible_plugin):
    def _create_adapter_from_ansible_plugin():
        return HashiVaultOptionAdapter.from_ansible_plugin(ansible_plugin)

    return _create_adapter_from_ansible_plugin


@pytest.fixture(params=[
    'dict',
    'dict_defaults',
    pytest.param('ansible_plugin', marks=option_adapter_from_plugin_marks),
])
def adapter(request, adapter_from_dict, adapter_from_dict_defaults, adapter_from_ansible_plugin):
    return {
        'dict': adapter_from_dict,
        'dict_defaults': adapter_from_dict_defaults,
        'ansible_plugin': adapter_from_ansible_plugin,
    }[request.param]()
