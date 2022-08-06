# -*- coding: utf-8 -*-
# Copyright (c) 2022 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
import pytest

import json

from .....plugins.modules import vault_token_create

pytestmark = pytest.mark.usefixtures(
    'patch_ansible_module',
    'patch_authenticator',
    'patch_get_vault_client',
)


def _connection_options():
    return {
        'auth_method': 'token',
        'url': 'http://myvault',
        'token': 'throwaway',
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


def _combined_options(**kwargs):
    opt = _connection_options()
    opt.update(_pass_thru_options())
    opt.update(kwargs)
    return opt


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

    @pytest.mark.no_ansible_module_patch
    def test_vault_token_create_passthru_options_expected(self, pass_thru_options):
        # designed to catch the case where new passthru options differ between tests and module

        module_set = set(vault_token_create.PASS_THRU_OPTION_NAMES)
        test_set = set(pass_thru_options.keys())

        assert sorted(vault_token_create.PASS_THRU_OPTION_NAMES) == sorted(pass_thru_options.keys()), (
            "Passthru options in module do not match options in test: %r" % (
                list(module_set ^ test_set)
            )
        )

    @pytest.mark.no_ansible_module_patch
    def test_vault_token_create_legacy_options_expected(self, legacy_option_translation, pass_thru_options):
        # designed to catch the case where new legacy translations differ between tests and module
        # and that all listed translations are present in passthru options

        module_set = set(vault_token_create.LEGACY_OPTION_TRANSLATION.items())
        test_set = set(legacy_option_translation.items())

        module_key_set = set(vault_token_create.LEGACY_OPTION_TRANSLATION.keys())
        pass_thru_key_set = set(pass_thru_options.keys())

        assert module_set == test_set, (
            "Legacy options in module do not match legacy options in test:\nmodule: %r\ntest: %r" % (
                dict(module_set - test_set),
                dict(test_set - module_set),
            )
        )
        assert vault_token_create.LEGACY_OPTION_TRANSLATION.keys() <= pass_thru_options.keys(), (
            "Legacy option translation keys must exist in passthru options: %r" % (
                list(module_key_set - pass_thru_key_set),
            )
        )

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options()], indirect=True)
    def test_vault_token_create_passthru_options(self, pass_thru_options, token_create_response, vault_client, capfd):
        client = vault_client
        client.auth.token.create.return_value = token_create_response

        with pytest.raises(SystemExit):
            vault_token_create.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        client.create_token.assert_not_called()
        client.auth.token.create.assert_called_once()

        assert result['login'] == token_create_response, (
            "module result did not match expected result:\nmodule: %r\nexpected: %r" % (result['login'], token_create_response)
        )

        if sys.version_info < (3, 8):
            # TODO: remove when python < 3.8 is dropped
            assert pass_thru_options.items() <= client.auth.token.create.call_args[1].items()
        else:
            assert pass_thru_options.items() <= client.auth.token.create.call_args.kwargs.items()

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options(orphan=True)], indirect=True)
    def test_vault_token_create_legacy_options(self, pass_thru_options, legacy_option_translation, token_create_response, vault_client, capfd):
        client = vault_client
        client.create_token.return_value = token_create_response

        with pytest.raises(SystemExit):
            vault_token_create.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        client.auth.token.create.assert_not_called()
        client.create_token.assert_called_once()

        assert result['login'] == token_create_response, (
            "module result did not match expected result:\nmodule: %r\nexpected: %r" % (result['module'], token_create_response)
        )

        if sys.version_info < (3, 8):
            # TODO: remove when python < 3.8 is dropped
            call_kwargs = client.create_token.call_args[1]
        else:
            call_kwargs = client.create_token.call_args.kwargs

        for name, legacy in legacy_option_translation.items():
            assert name not in call_kwargs, (
                "'%s' was found in call to legacy method, should be '%s'" % (name, legacy)
            )
            assert legacy in call_kwargs, (
                "'%s' (from '%s') was not found in call to legacy method" % (legacy, name)
            )
            assert call_kwargs[legacy] == pass_thru_options.get(name), (
                "Expected legacy param '%s' not found or value did not match:\nvalue: %r\nexpected: %r" % (
                    legacy,
                    call_kwargs.get(legacy),
                    pass_thru_options.get(name),
                )
            )

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options(orphan=True)], indirect=True)
    def test_vault_token_create_legacy_fallback(self, pass_thru_options, token_create_response, vault_client, module_warn, capfd):
        client = vault_client
        client.create_token.side_effect = AttributeError
        client.auth.token.create.return_value = token_create_response

        with pytest.raises(SystemExit):
            vault_token_create.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        module_warn.assert_called_once_with("'create_token' method was not found. Attempting method that requires root privileges.")
        client.auth.token.create.assert_called_once()

        assert result['login'] == token_create_response, (
            "module result did not match expected result:\nmodule: %r\nexpected: %r" % (result['login'], token_create_response)
        )

        # we're retesting that expected options were passed, even though there's a separate test for that,
        # to ensure that nothing in the original legacy attempt mutates the non-legacy options during fallback
        if sys.version_info < (3, 8):
            # TODO: remove when python < 3.8 is dropped
            assert pass_thru_options.items() <= client.auth.token.create.call_args[1].items()
        else:
            assert pass_thru_options.items() <= client.auth.token.create.call_args.kwargs.items()
