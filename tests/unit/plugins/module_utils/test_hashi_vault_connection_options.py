# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import pytest

from ansible_collections.community.hashi_vault.tests.unit.compat import mock

from ansible_collections.community.hashi_vault.plugins.module_utils.hashi_vault_common import (
    HashiVaultOptionGroupBase,
    HashiVaultConnectionOptions,
    HashiVaultOptionAdapter,
)


CONNECTION_OPTIONS = {
    'url': 'https://127.0.0.1',
    'proxies': None,
    'namespace': None,
    'validate_certs': None,
    'ca_cert': None,
}

@pytest.fixture
def predefined_options():
    return CONNECTION_OPTIONS.copy()


@pytest.fixture
def adapter(predefined_options):
    return HashiVaultOptionAdapter.from_dict(predefined_options)


@pytest.fixture
def connection_options(adapter):
    return HashiVaultConnectionOptions(adapter)


class TestHashiVaultConnectionOptions(object):
    def test_connection_options_is_option_group(self, connection_options):
        assert issubclass(type(connection_options), HashiVaultOptionGroupBase)

    # _boolean_or_cacert tests
    # this method is the intersection of the validate_certs and ca_cert parameter
    # along with the VAULT_SKIP_VERIFY environment variable (see the function defintion).
    # The result is either a boolean, or a string, to be passed to the hvac client's
    # verify parameter.

    @pytest.mark.parametrize(
        'optpatch,envpatch,expected',
        [
            ({}, {}, True),
            ({}, {'VAULT_SKIP_VERIFY': 'true'}, False),
            ({}, {'VAULT_SKIP_VERIFY': 'false'}, True),
            ({}, {'VAULT_SKIP_VERIFY': 'invalid'}, True),
            ({'validate_certs': True}, {}, True),
            ({'validate_certs': True}, {'VAULT_SKIP_VERIFY': 'false'}, True),
            ({'validate_certs': True}, {'VAULT_SKIP_VERIFY': 'true'}, True),
            ({'validate_certs': True}, {'VAULT_SKIP_VERIFY': 'invalid'}, True),
            ({'validate_certs': False}, {}, False),
            ({'validate_certs': False}, {'VAULT_SKIP_VERIFY': 'false'}, False),
            ({'validate_certs': False}, {'VAULT_SKIP_VERIFY': 'true'}, False),
            ({'validate_certs': False}, {'VAULT_SKIP_VERIFY': 'invalid'}, False),
            ({'ca_cert': '/tmp/fake'}, {}, '/tmp/fake'),
            ({'ca_cert': '/tmp/fake'}, {'VAULT_SKIP_VERIFY': 'true'}, False),
            ({'ca_cert': '/tmp/fake'}, {'VAULT_SKIP_VERIFY': 'false'}, '/tmp/fake'),
            ({'ca_cert': '/tmp/fake'}, {'VAULT_SKIP_VERIFY': 'invalid'}, '/tmp/fake'),
            ({'ca_cert': '/tmp/fake', 'validate_certs': True}, {}, '/tmp/fake'),
            ({'ca_cert': '/tmp/fake', 'validate_certs': True}, {'VAULT_SKIP_VERIFY': 'false'}, '/tmp/fake'),
            ({'ca_cert': '/tmp/fake', 'validate_certs': True}, {'VAULT_SKIP_VERIFY': 'true'}, '/tmp/fake'),
            ({'ca_cert': '/tmp/fake', 'validate_certs': True}, {'VAULT_SKIP_VERIFY': 'invalid'}, '/tmp/fake'),
            ({'ca_cert': '/tmp/fake', 'validate_certs': False}, {}, False),
            ({'ca_cert': '/tmp/fake', 'validate_certs': False}, {'VAULT_SKIP_VERIFY': 'false'}, False),
            ({'ca_cert': '/tmp/fake', 'validate_certs': False}, {'VAULT_SKIP_VERIFY': 'true'}, False),
            ({'ca_cert': '/tmp/fake', 'validate_certs': False}, {'VAULT_SKIP_VERIFY': 'invalid'}, False),
        ]
    )
    def test_boolean_or_cacert(self, connection_options, predefined_options, adapter, optpatch, envpatch, expected):
        adapter.set_options(**optpatch)

        with mock.patch.dict(os.environ, envpatch):
            connection_options._boolean_or_cacert()

        assert predefined_options['ca_cert'] == expected
