# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import contextlib

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

    def __init__(self, option_adapter, warning_callback, deprecate_callback):
        super(HashiVaultAuthMethodFake, self).__init__(option_adapter, warning_callback, deprecate_callback)

    validate = mock.MagicMock()
    authenticate = mock.MagicMock()


@pytest.fixture
def option_dict():
    return {'auth_method': 'fake'}


@pytest.fixture
def adapter(option_dict):
    return HashiVaultOptionAdapter.from_dict(option_dict)


@pytest.fixture
def fake_auth_class(adapter, warner, deprecator):
    return HashiVaultAuthMethodFake(adapter, warner, deprecator)


@pytest.fixture
def client():
    return hvac.Client()


@pytest.fixture
def warner():
    return mock.MagicMock()


@pytest.fixture
def deprecator():
    return mock.MagicMock()


@pytest.fixture
def mock_import_error():
    @contextlib.contextmanager
    def _mock_import_error(*names):
        import builtins

        real_import = builtins.__import__

        def _fake_importer(name, *args, **kwargs):
            if name in names:
                raise ImportError

            return real_import(name, *args, **kwargs)

        with mock.patch.object(builtins, '__import__', side_effect=_fake_importer):
            yield

    return _mock_import_error
