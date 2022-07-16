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
def legacy_option_translation():
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

    def test_vault_token_create_legacy_options_expected(self, vault_token_create_lookup, legacy_option_translation, pass_thru_options):
        # designed to catch the case where new legacy translations differ between tests and lookup
        # and that all listed translations are present in passthru options

        lookup_set = set(vault_token_create_lookup.LEGACY_OPTION_TRANSLATION.items())
        test_set = set(legacy_option_translation.items())

        lookup_key_set = set(vault_token_create_lookup.LEGACY_OPTION_TRANSLATION.keys())
        pass_thru_key_set = set(pass_thru_options.keys())

        assert lookup_set == test_set, (
            "Legacy options in lookup do not match legacy options in test:\nlookup: %r\ntest: %r" % (
                dict(lookup_set - test_set),
                dict(test_set - lookup_set),
            )
        )
        assert vault_token_create_lookup.LEGACY_OPTION_TRANSLATION.keys() <= pass_thru_options.keys(), (
            "Legacy option translation keys must exist in passthru options: %r" % (
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

    def test_vault_token_create_legacy_options(
        self, vault_token_create_lookup, authenticator, minimal_vars, pass_thru_options, legacy_option_translation, token_create_response
    ):

        client = mock.MagicMock()
        client.create_token.return_value = token_create_response

        with mock.patch.object(vault_token_create_lookup, 'authenticator', new=authenticator):
            with mock.patch.object(vault_token_create_lookup.helper, 'get_vault_client', return_value=client):
                result = vault_token_create_lookup.run(terms=[], variables=minimal_vars, orphan=True, **pass_thru_options)

                client.auth.token.create.assert_not_called()
                client.create_token.assert_called_once()

                assert result[0] == token_create_response, (
                    "lookup result did not match expected result:\nlookup: %r\nexpected: %r" % (result, token_create_response)
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

    def test_vault_token_create_legacy_fallback(self, vault_token_create_lookup, authenticator, minimal_vars, pass_thru_options, token_create_response):
        client = mock.MagicMock()
        client.create_token.side_effect = AttributeError
        client.auth.token.create.return_value = token_create_response

        with mock.patch('ansible_collections.community.hashi_vault.plugins.lookup.vault_token_create.display.warning') as warning:
            with mock.patch.object(vault_token_create_lookup, 'authenticator', new=authenticator):
                with mock.patch.object(vault_token_create_lookup.helper, 'get_vault_client', return_value=client):
                    result = vault_token_create_lookup.run(terms=[], variables=minimal_vars, orphan=True, **pass_thru_options)

                    warning.assert_called_once_with("'create_token' method was not found. Attempting method that requires root privileges.")
                    client.auth.token.create.assert_called_once()

                    assert result[0] == token_create_response, (
                        "lookup result did not match expected result:\nlookup: %r\nexpected: %r" % (result, token_create_response)
                    )

                    # we're retesting that expected options were passed, even though there's a separate test for that,
                    # to ensure that nothing in the original legacy attempt mutates the non-legacy options during fallback
                    if sys.version_info < (3, 8):
                        # TODO: remove when python < 3.8 is dropped
                        assert pass_thru_options.items() <= client.auth.token.create.call_args[1].items()
                    else:
                        assert pass_thru_options.items() <= client.auth.token.create.call_args.kwargs.items()
