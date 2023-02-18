# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ......plugins.module_utils._auth_method_none import HashiVaultAuthMethodNone
from ......plugins.module_utils._hashi_vault_common import HashiVaultAuthMethodBase


@pytest.fixture
def auth_none(adapter, warner, deprecator):
    return HashiVaultAuthMethodNone(adapter, warner, deprecator)


class TestAuthNone(object):

    def test_auth_none_is_auth_method_base(self, auth_none):
        assert issubclass(type(auth_none), HashiVaultAuthMethodBase)

    def test_auth_none_validate(self, auth_none):
        auth_none.validate()

    @pytest.mark.parametrize('use_token', [True, False])
    def test_auth_none_authenticate(self, auth_none, client, use_token):
        result = auth_none.authenticate(client, use_token=use_token)

        assert result is None
        assert client.token is None
