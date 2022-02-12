# -*- coding: utf-8 -*-
# Copyright (c) 2022 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
import pytest

import json

from ansible_collections.community.hashi_vault.tests.unit.compat import mock
from .....plugins.modules import vault_token_create

pytestmark = pytest.mark.usefixtures(
    'patch_ansible_module',
    'patch_authenticator',
    'patch_get_vault_client',
)


def _connection_options():
    return {
        'auth_method': 'token',
        'url': 'http://dummy',
        'token': 'dummy',
    }


def _pass_thru_options():
    return {
        'no_parent': True,
        'no_default_policy': True,
        'policies': ['a', 'b'],
        'id': 'tokenid',
        'role_name': 'role',
        'meta': {'a': 'valA', 'b': 'valB'},
        'renewable': True,
        'ttl': '1h',
        'type': 'batch',
        'explicit_max_ttl': '2h',
        'display_name': 'kiminonamae',
        'num_uses': 9,
        'period': '8h',
        'entity_alias': 'alias',
        'wrap_ttl': '60s',
    }


def _combined_options():
    opt = _connection_options()
    opt.update(_pass_thru_options())
    return opt


@pytest.fixture
def connection_options():
    return _connection_options()


@pytest.fixture
def pass_thru_options():
    return _pass_thru_options()


@pytest.fixture
def legacy_option_translation():
    return {
        'id': 'token_id',
        'role_name': 'role',
        'type': 'token_type',
    }


@pytest.fixture
def token_create_response(fixture_loader):
    return fixture_loader('token_create_response.json')


class TestModuleVaultTokenCreate():

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options()], indirect=True)
    def test_run(self, pass_thru_options, token_create_response, vault_client, capfd):
        client = vault_client
        client.auth.token.create.return_value = token_create_response

        with pytest.raises(SystemExit):
            vault_token_create.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        client.create_token.assert_not_called()
        client.auth.token.create.assert_called_once()

        assert result['login'] == token_create_response

        if sys.version_info < (3, 8):
            # TODO: remove when python < 3.8 is dropped
            assert pass_thru_options.items() <= client.auth.token.create.call_args[1].items()
        else:
            assert pass_thru_options.items() <= client.auth.token.create.call_args.kwargs.items()
