# -*- coding: utf-8 -*-
# Copyright (c) 2022 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
import pytest

from ansible.plugins.loader import lookup_loader
from ansible.errors import AnsibleError

from ansible_collections.community.hashi_vault.tests.unit.compat import mock

from ansible_collections.community.hashi_vault.plugins.plugin_utils._hashi_vault_lookup_base import HashiVaultLookupBase

from .....plugins.lookup import vault_token_create
from .....plugins.module_utils._hashi_vault_common import HashiVaultValueError


pytest.importorskip('hvac')


pytestmark = pytest.mark.usefixtures(
    'patch_authenticator',
    'patch_get_vault_client',
)


@pytest.fixture
def vault_token_create_lookup():
    return lookup_loader.get('community.hashi_vault.vault_token_create')


@pytest.fixture
def pass_thru_options():
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


class TestVaultTokenCreateLookup(object):

    def test_vault_token_create_is_lookup_base(self, vault_token_create_lookup):
        assert issubclass(type(vault_token_create_lookup), HashiVaultLookupBase)

    def test_vault_token_create_no_hvac(self, vault_token_create_lookup, minimal_vars):
        with mock.patch.object(vault_token_create, 'HVAC_IMPORT_ERROR', new=ImportError()):
            with pytest.raises(AnsibleError, match=r"This plugin requires the 'hvac' Python library"):
                vault_token_create_lookup.run(terms='fake', variables=minimal_vars)

    @pytest.mark.parametrize('exc', [HashiVaultValueError('throwaway msg'), NotImplementedError('throwaway msg')])
    def test_vault_token_create_authentication_error(self, vault_token_create_lookup, minimal_vars, authenticator, exc):
        authenticator.authenticate.side_effect = exc

        with pytest.raises(AnsibleError, match=r'throwaway msg'):
            vault_token_create_lookup.run(terms='fake', variables=minimal_vars)

    @pytest.mark.parametrize('exc', [HashiVaultValueError('throwaway msg'), NotImplementedError('throwaway msg')])
    def test_vault_token_create_auth_validation_error(self, vault_token_create_lookup, minimal_vars, authenticator, exc):
        authenticator.validate.side_effect = exc

        with pytest.raises(AnsibleError, match=r'throwaway msg'):
            vault_token_create_lookup.run(terms='fake', variables=minimal_vars)

    def test_vault_token_create_extra_terms(self, vault_token_create_lookup, authenticator, minimal_vars):
        with mock.patch('ansible_collections.community.hashi_vault.plugins.lookup.vault_token_create.display.warning') as warning:
            with mock.patch.object(vault_token_create_lookup, 'authenticator', new=authenticator):
                with mock.patch.object(vault_token_create_lookup.helper, 'get_vault_client'):
                    vault_token_create_lookup.run(terms=['', ''], variables=minimal_vars)
                    warning.assert_called_once_with("Supplied term strings will be ignored. This lookup does not use term strings.")

    def test_vault_token_create_passthru_options_expected(self, vault_token_create_lookup, pass_thru_options):
        # designed to catch the case where new passthru options differ between tests and lookup

        lookup_set = set(vault_token_create_lookup.PASS_THRU_OPTION_NAMES)
        test_set = set(pass_thru_options.keys())

        assert sorted(vault_token_create_lookup.PASS_THRU_OPTION_NAMES) == sorted(pass_thru_options.keys()), (
            "Passthru options in lookup do not match options in test: %r" % (
                list(lookup_set ^ test_set)
            )
        )

    def test_vault_token_create_orphan_options_expected(self, vault_token_create_lookup, orphan_option_translation, pass_thru_options):
        # designed to catch the case where new orphan translations differ between tests and lookup
        # and that all listed translations are present in passthru options

        lookup_set = set(vault_token_create_lookup.ORPHAN_OPTION_TRANSLATION.items())
        test_set = set(orphan_option_translation.items())

        lookup_key_set = set(vault_token_create_lookup.ORPHAN_OPTION_TRANSLATION.keys())
        pass_thru_key_set = set(pass_thru_options.keys())

        assert lookup_set == test_set, (
            "Orphan options in lookup do not match orphan options in test:\nlookup: %r\ntest: %r" % (
                dict(lookup_set - test_set),
                dict(test_set - lookup_set),
            )
        )
        assert vault_token_create_lookup.ORPHAN_OPTION_TRANSLATION.keys() <= pass_thru_options.keys(), (
            "Orphan option translation keys must exist in passthru options: %r" % (
                list(lookup_key_set - pass_thru_key_set),
            )
        )

    def test_vault_token_create_passthru_options(self, vault_token_create_lookup, authenticator, minimal_vars, pass_thru_options, token_create_response):

        client = mock.MagicMock()
        client.auth.token.create.return_value = token_create_response

        with mock.patch.object(vault_token_create_lookup, 'authenticator', new=authenticator):
            with mock.patch.object(vault_token_create_lookup.helper, 'get_vault_client', return_value=client):
                result = vault_token_create_lookup.run(terms=[], variables=minimal_vars, **pass_thru_options)

                client.create_token.assert_not_called()
                client.auth.token.create.assert_called_once()

                assert result[0] == token_create_response, (
                    "lookup result did not match expected result:\nlookup: %r\nexpected: %r" % (result, token_create_response)
                )

                if sys.version_info < (3, 8):
                    # TODO: remove when python < 3.8 is dropped
                    assert pass_thru_options.items() <= client.auth.token.create.call_args[1].items()
                else:
                    assert pass_thru_options.items() <= client.auth.token.create.call_args.kwargs.items()

    def test_vault_token_create_orphan_options(
        self, vault_token_create_lookup, authenticator, minimal_vars, pass_thru_options, orphan_option_translation, token_create_response
    ):

        client = mock.MagicMock()
        client.auth.token.create_orphan.return_value = token_create_response

        with mock.patch.object(vault_token_create_lookup, 'authenticator', new=authenticator):
            with mock.patch.object(vault_token_create_lookup.helper, 'get_vault_client', return_value=client):
                result = vault_token_create_lookup.run(terms=[], variables=minimal_vars, orphan=True, **pass_thru_options)

                client.auth.token.create.assert_not_called()
                client.auth.token.create_orphan.assert_called_once()
                client.create_token.assert_not_called()

                assert result[0] == token_create_response, (
                    "lookup result did not match expected result:\nlookup: %r\nexpected: %r" % (result, token_create_response)
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

    def test_vault_token_create_orphan_fallback(self, vault_token_create_lookup, authenticator, minimal_vars, pass_thru_options, token_create_response):
        client = mock.MagicMock()
        client.create_token.return_value = token_create_response
        client.auth.token.create_orphan.side_effect = AttributeError

        with mock.patch.object(vault_token_create_lookup, 'authenticator', new=authenticator):
            with mock.patch.object(vault_token_create_lookup.helper, 'get_vault_client', return_value=client):
                result = vault_token_create_lookup.run(terms=[], variables=minimal_vars, orphan=True, **pass_thru_options)

                client.auth.token.create_orphan.assert_called_once()
                client.create_token.assert_called_once()

                assert result[0] == token_create_response, (
                    "lookup result did not match expected result:\nlookup: %r\nexpected: %r" % (result, token_create_response)
                )

    def test_vault_token_create_exception_handling_standard(self, vault_token_create_lookup, authenticator, minimal_vars, pass_thru_options):
        client = mock.MagicMock()
        client.auth.token.create.side_effect = Exception('side_effect')

        with mock.patch.object(vault_token_create_lookup, 'authenticator', new=authenticator):
            with mock.patch.object(vault_token_create_lookup.helper, 'get_vault_client', return_value=client):
                with pytest.raises(AnsibleError, match=r'^side_effect$'):
                    vault_token_create_lookup.run(terms=[], variables=minimal_vars, **pass_thru_options)

    def test_vault_token_create_exception_handling_orphan(self, vault_token_create_lookup, authenticator, minimal_vars, pass_thru_options):
        client = mock.MagicMock()
        client.auth.token.create_orphan.side_effect = Exception('side_effect')

        with mock.patch.object(vault_token_create_lookup, 'authenticator', new=authenticator):
            with mock.patch.object(vault_token_create_lookup.helper, 'get_vault_client', return_value=client):
                with pytest.raises(AnsibleError, match=r'^side_effect$'):
                    vault_token_create_lookup.run(terms=[], variables=minimal_vars, orphan=True, **pass_thru_options)

    def test_vault_token_create_exception_handling_orphan_fallback(self, vault_token_create_lookup, authenticator, minimal_vars, pass_thru_options):
        client = mock.MagicMock()
        client.create_token.side_effect = Exception('side_effect')
        client.auth.token.create_orphan.side_effect = AttributeError

        with mock.patch.object(vault_token_create_lookup, 'authenticator', new=authenticator):
            with mock.patch.object(vault_token_create_lookup.helper, 'get_vault_client', return_value=client):
                with pytest.raises(AnsibleError, match=r'^side_effect$'):
                    vault_token_create_lookup.run(terms=[], variables=minimal_vars, orphan=True, **pass_thru_options)
