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
from .....plugins.module_utils._hashi_vault_common import HashiVaultValueError

pytestmark = pytest.mark.usefixtures(
    'patch_ansible_module',
    'patch_authenticator',
    'patch_get_vault_client',
)


def _connection_options():
    return {
        'auth_method': 'token',
        'url': 'http://myvault',
        'token': 'rando',
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
def orphan_option_translation():
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
    @pytest.mark.parametrize('exc', [HashiVaultValueError('throwaway msg'), NotImplementedError('throwaway msg')])
    def test_vault_token_create_authentication_error(self, authenticator, exc, capfd):
        authenticator.authenticate.side_effect = exc

        with pytest.raises(SystemExit) as e:
            vault_token_create.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)
        assert result['msg'] == 'throwaway msg', "result: %r" % result

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options()], indirect=True)
    @pytest.mark.parametrize('exc', [HashiVaultValueError('throwaway msg'), NotImplementedError('throwaway msg')])
    def test_vault_token_create_auth_validation_error(self, authenticator, exc, capfd):
        authenticator.validate.side_effect = exc

        with pytest.raises(SystemExit) as e:
            vault_token_create.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)
        assert result['msg'] == 'throwaway msg'

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
    def test_vault_token_create_orphan_options_expected(self, orphan_option_translation, pass_thru_options):
        # designed to catch the case where new orphan translations differ between tests and module
        # and that all listed translations are present in passthru options

        module_set = set(vault_token_create.ORPHAN_OPTION_TRANSLATION.items())
        test_set = set(orphan_option_translation.items())

        module_key_set = set(vault_token_create.ORPHAN_OPTION_TRANSLATION.keys())
        pass_thru_key_set = set(pass_thru_options.keys())

        assert module_set == test_set, (
            "Orphan options in module do not match orphan options in test:\nmodule: %r\ntest: %r" % (
                dict(module_set - test_set),
                dict(test_set - module_set),
            )
        )
        assert vault_token_create.ORPHAN_OPTION_TRANSLATION.keys() <= pass_thru_options.keys(), (
            "Orphan option translation keys must exist in passthru options: %r" % (
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
        client.auth.token.create_orphan.assert_not_called()
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
    def test_vault_token_create_orphan_options(self, pass_thru_options, orphan_option_translation, token_create_response, vault_client, capfd):
        client = vault_client
        client.auth.token.create_orphan.return_value = token_create_response

        with pytest.raises(SystemExit):
            vault_token_create.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        client.create_token.assert_not_called()
        client.auth.token.create.assert_not_called()
        client.auth.token.create_orphan.assert_called_once()

        assert result['login'] == token_create_response, (
            "module result did not match expected result:\nmodule: %r\nexpected: %r" % (result['module'], token_create_response)
        )

        if sys.version_info < (3, 8):
            # TODO: remove when python < 3.8 is dropped
            call_kwargs = client.auth.token.create_orphan.call_args[1]
        else:
            call_kwargs = client.auth.token.create_orphan.call_args.kwargs

        for name, orphan in orphan_option_translation.items():
            assert name not in call_kwargs, (
                "'%s' was found in call to orphan method, should be '%s'" % (name, orphan)
            )
            assert orphan in call_kwargs, (
                "'%s' (from '%s') was not found in call to orphan method" % (orphan, name)
            )
            assert call_kwargs[orphan] == pass_thru_options.get(name), (
                "Expected orphan param '%s' not found or value did not match:\nvalue: %r\nexpected: %r" % (
                    orphan,
                    call_kwargs.get(orphan),
                    pass_thru_options.get(name),
                )
            )

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options(orphan=True)], indirect=True)
    def test_vault_token_create_orphan_fallback(self, token_create_response, vault_client, capfd):
        client = vault_client
        client.create_token.return_value = token_create_response
        client.auth.token.create_orphan.side_effect = AttributeError

        with pytest.raises(SystemExit):
            vault_token_create.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        client.auth.token.create_orphan.assert_called_once()
        client.create_token.assert_called_once()

        assert result['login'] == token_create_response, (
            "module result did not match expected result:\nmodule: %r\nexpected: %r" % (result['login'], token_create_response)
        )

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options()], indirect=True)
    def test_vault_token_create_exception_handling_standard(self, vault_client, capfd):
        client = vault_client
        client.auth.token.create.side_effect = Exception('side_effect')

        with pytest.raises(SystemExit) as e:
            vault_token_create.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)
        assert result['msg'] == 'side_effect'

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options(orphan=True)], indirect=True)
    def test_vault_token_create_exception_handling_orphan(self, vault_client, capfd):
        client = vault_client
        client.auth.token.create_orphan.side_effect = Exception('side_effect')

        with pytest.raises(SystemExit) as e:
            vault_token_create.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)
        assert result['msg'] == 'side_effect'

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options(orphan=True)], indirect=True)
    def test_vault_token_create_exception_handling_orphan_fallback(self, vault_client, capfd):
        client = vault_client
        client.create_token.side_effect = Exception('side_effect')
        client.auth.token.create_orphan.side_effect = AttributeError

        with pytest.raises(SystemExit) as e:
            vault_token_create.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)
        assert result['msg'] == 'side_effect'
