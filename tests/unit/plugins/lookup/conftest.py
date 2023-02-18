# Copyright (c) 2022 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest


@pytest.fixture
def minimal_vars():
    return {
        'ansible_hashi_vault_auth_method': 'token',
        'ansible_hashi_vault_url': 'http://myvault',
        'ansible_hashi_vault_token': 'throwaway',
    }
