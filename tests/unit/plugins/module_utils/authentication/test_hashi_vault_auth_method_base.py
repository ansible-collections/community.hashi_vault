# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
import pytest

from ansible_collections.community.hashi_vault.tests.unit.compat import mock

from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import (
    HashiVaultAuthMethodBase,
    HashiVaultOptionGroupBase,
    HashiVaultValueError,
)


@pytest.fixture
def auth_base(adapter, warner):
    return HashiVaultAuthMethodBase(adapter, warner)


class TestHashiVaultAuthMethodBase(object):

    def test_auth_method_is_option_group_base(self, fake_auth_class):
        assert issubclass(type(fake_auth_class), HashiVaultOptionGroupBase)

    def test_base_validate_not_implemented(self, auth_base):
        with pytest.raises(NotImplementedError):
            auth_base.validate()

    def test_base_authenticate_not_implemented(self, auth_base, client):
        with pytest.raises(NotImplementedError):
            auth_base.authenticate(client)

    @pytest.mark.parametrize('options,required', [
        ({}, []),
        ({'a': 1, 'b': '2'}, ['b']),
        ({'a': 1, 'b': '2'}, ['a', 'b']),
        ({'a': 1, 'b': '2', 'c': 3.0}, ['a', 'c'])
    ])
    def test_validate_by_required_fields_success(self, auth_base, adapter, options, required):
        adapter.set_options(**options)

        auth_base.validate_by_required_fields(*required)

    @pytest.mark.parametrize('options,required', [
        ({}, ['a']),
        ({'a': 1, 'b': '2'}, ['c']),
        ({'a': 1, 'b': '2'}, ['a', 'c']),
        ({'a': 1, 'b': '2', 'c': 3.0}, ['a', 'c', 'd'])
    ])
    def test_validate_by_required_fields_failure(self, fake_auth_class, adapter, options, required):
        adapter.set_options(**options)

        with pytest.raises(HashiVaultValueError):
            fake_auth_class.validate_by_required_fields(*required)

    def test_warning_callback(self, auth_base, warner):
        msg = 'warning msg'

        auth_base.warn(msg)

        warner.assert_called_once_with(msg)
