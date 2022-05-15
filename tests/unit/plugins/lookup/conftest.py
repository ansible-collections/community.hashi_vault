# Copyright (c) 2022 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ...compat import mock


@pytest.fixture
def minimal_vars():
    return {
        'ansible_hashi_vault_auth_method': 'token',
        'ansible_hashi_vault_url': 'http://myvault',
        'ansible_hashi_vault_token': 'throwaway',
    }
