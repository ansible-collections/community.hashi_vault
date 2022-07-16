# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
import os
import json
import pytest

from .compat import mock

from ...plugins.module_utils._authenticator import HashiVaultAuthenticator


@pytest.fixture(autouse=True)
def skip_python():
    if sys.version_info < (3, 6):
        pytest.skip('Skipping on Python %s. community.hashi_vault supports Python 3.6 and higher.' % sys.version)


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


@pytest.fixture
def vault_client():
    return mock.MagicMock()


@pytest.fixture
def authenticator():
    authenticator = HashiVaultAuthenticator
    authenticator.validate = mock.Mock(wraps=lambda: True)
    authenticator.authenticate = mock.Mock(wraps=lambda client: 'throwaway')

    return authenticator


@pytest.fixture
def patch_authenticator(authenticator):
    with mock.patch('ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_module.HashiVaultAuthenticator', new=authenticator):
        yield


@pytest.fixture
def patch_get_vault_client(vault_client):
    with mock.patch(
        'ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common.HashiVaultHelper.get_vault_client', return_value=vault_client
    ):
        yield


@pytest.fixture
def requests_unparseable_response():
    r = mock.MagicMock()
    r.json.side_effect = json.JSONDecodeError

    return r
