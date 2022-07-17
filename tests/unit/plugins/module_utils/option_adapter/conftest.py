# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

# this file must define the "adapter" fixture at a minimum,
# and anything else that it needs or depends on that isn't already defined in in the test files themselves.

# Keep in mind that this one is for module_utils and so it cannot depend on or import any controller-side code.

from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import HashiVaultOptionAdapter

import pytest


class FakeAnsibleModule:
    '''HashiVaultOptionAdapter.from_ansible_module() only cares about the AnsibleModule.params dict'''

    def __init__(self, params):
        self.params = params


@pytest.fixture
def ansible_module(sample_dict):
    return FakeAnsibleModule(sample_dict)


@pytest.fixture
def adapter_from_ansible_module(ansible_module):
    def _create_adapter_from_ansible_module():
        return HashiVaultOptionAdapter.from_ansible_module(ansible_module)

    return _create_adapter_from_ansible_module


@pytest.fixture(params=['dict', 'dict_defaults', 'ansible_module'])
def adapter(request, adapter_from_dict, adapter_from_dict_defaults, adapter_from_ansible_module):
    return {
        'dict': adapter_from_dict,
        'dict_defaults': adapter_from_dict_defaults,
        'ansible_module': adapter_from_ansible_module,
    }[request.param]()
