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

    @pytest.mark.parametrize('has_import', [True])
    @pytest.mark.parametrize('should_warn', [True, False])
    def test_check_import_has_import(self, auth_base, warner, has_import, should_warn):
        result = auth_base.check_import('namename', has_import, warn=should_warn)

        assert result is None
        warner.assert_not_called()

    @pytest.mark.parametrize('has_import', [False])
    def test_check_import_has_not_raises(self, auth_base, warner, has_import):
        with pytest.raises(ImportError):
            auth_base.check_import('namename', has_import)

        warner.assert_not_called()

    @pytest.mark.parametrize('has_import', [False])
    def test_check_import_has_not_warns(self, auth_base, warner, has_import):
        auth_base.check_import('namename', has_import, warn=True)

        # TODO: revisit in 2.0.0 when py3.5 is dropped (see https://github.com/ansible-collections/community.hashi_vault/issues/81)
        # for now we will keep the conditional so that the intended code is ready
        if sys.version_info < (3, 6):
            assert warner.call_count == 1
        else:
            warner.assert_called_once()
