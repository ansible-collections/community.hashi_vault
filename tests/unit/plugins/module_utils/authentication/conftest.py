# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json
import pytest

try:
    import hvac
except ImportError:
    # python 2.6, which isn't supported anyway
    pass

from ansible_collections.community.hashi_vault.tests.unit.compat import mock

from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import (
    HashiVaultAuthMethodBase,
    HashiVaultOptionAdapter,
)


class HashiVaultAuthMethodFake(HashiVaultAuthMethodBase):
    NAME = 'fake'
    OPTIONS = []

    def __init__(self, option_adapter, warning_callback):
        super(HashiVaultAuthMethodFake, self).__init__(option_adapter, warning_callback)

    validate = mock.MagicMock()
    authenticate = mock.MagicMock()


@pytest.fixture
def option_dict():
    return {'auth_method': 'fake'}


@pytest.fixture
def adapter(option_dict):
    return HashiVaultOptionAdapter.from_dict(option_dict)


@pytest.fixture
def fake_auth_class(adapter):
    return HashiVaultAuthMethodFake(adapter, mock.MagicMock())


@pytest.fixture
def client():
    return hvac.Client()


@pytest.fixture
def warner():
    return mock.MagicMock()


@pytest.fixture
def fixture_loader():
    def _loader(name, parse='json'):
        here = os.path.dirname(os.path.realpath(__file__))
        fixture = os.path.join(here, 'fixtures', name)

        if parse == 'path':
            return fixture

        with open(fixture, 'r') as f:
            if parse == 'json':
                d = json.load(f)
            elif parse == 'lines':
                d = f.readlines()
            elif parse == 'raw':
                d = f.read()
            else:
                raise ValueError("Unknown value '%s' for parse" % parse)

        return d

    return _loader
