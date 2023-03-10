# -*- coding: utf-8 -*-
# Copyright (c) 2022 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible.utils.unsafe_proxy import AnsibleUnsafe, AnsibleUnsafeBytes, AnsibleUnsafeText

from ansible_collections.community.hashi_vault.tests.unit.compat import mock

from ansible_collections.community.hashi_vault.plugins.module_utils._auth_method_token import (
    HashiVaultAuthMethodToken,
)


@pytest.fixture
def option_dict():
    return {
        'auth_method': 'fake',
        'token': None,
        'token_path': None,
        'token_file': '.vault-token',
        'token_validate': True,
    }


@pytest.fixture(params=[AnsibleUnsafeBytes(b'ub_opaque'), AnsibleUnsafeText(u'ut_opaque'), b'b_opaque', u't_opaque'])
def stringy(request):
    return request.param


@pytest.fixture
def auth_token(adapter, warner, deprecator):
    return HashiVaultAuthMethodToken(adapter, warner, deprecator)


class TestAuthToken(object):
    def test_auth_token_unsafes(self, auth_token, client, adapter, stringy):
        adapter.set_option('token', stringy)
        adapter.set_option('token_validate', False)

        wrapper = mock.Mock(wraps=auth_token._stringify)

        with mock.patch.object(auth_token, '_stringify', wrapper):
            response = auth_token.authenticate(client, use_token=True, lookup_self=False)

        assert isinstance(response['auth']['client_token'], (bytes, type(u''))), repr(response['auth']['client_token'])
        assert isinstance(client.token, (bytes, type(u''))), repr(client.token)
        assert not isinstance(response['auth']['client_token'], AnsibleUnsafe), repr(response['auth']['client_token'])
        assert not isinstance(client.token, AnsibleUnsafe), repr(client.token)
