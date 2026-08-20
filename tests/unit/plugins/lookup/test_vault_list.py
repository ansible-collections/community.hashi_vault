# -*- coding: utf-8 -*-
# Copyright (c) 2023 Tom Kivlin (@tomkivlin)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible.plugins.loader import lookup_loader
from ansible.errors import AnsibleError

from ...compat import mock

from .....plugins.plugin_utils._hashi_vault_lookup_base import HashiVaultLookupBase
from .....plugins.module_utils._hashi_vault_common import HashiVaultValueError


hvac = pytest.importorskip('hvac')


pytestmark = pytest.mark.usefixtures(
    'patch_authenticator',
    'patch_get_vault_client',
)


@pytest.fixture
def vault_list_lookup():
    return lookup_loader.get('community.hashi_vault.vault_list')


LIST_FIXTURES = [
    'kv2_list_response.json',
    'policy_list_response.json',
    'userpass_list_response.json',
]


@pytest.fixture(params=LIST_FIXTURES)
def list_response(request, fixture_loader):
    return fixture_loader(request.param)


class TestVaultListLookup(object):

    def test_vault_list_is_lookup_base(self, vault_list_lookup):
        assert issubclass(type(vault_list_lookup), HashiVaultLookupBase)

    @pytest.mark.parametrize('exc', [HashiVaultValueError('throwaway msg'), NotImplementedError('throwaway msg')])
    def test_vault_list_authentication_error(self, vault_list_lookup, minimal_vars, authenticator, exc):
        authenticator.authenticate.side_effect = exc

        with pytest.raises(AnsibleError, match=r'throwaway msg'):
            vault_list_lookup.run(terms='fake', variables=minimal_vars)

    @pytest.mark.parametrize('exc', [HashiVaultValueError('throwaway msg'), NotImplementedError('throwaway msg')])
    def test_vault_list_auth_validation_error(self, vault_list_lookup, minimal_vars, authenticator, exc):
        authenticator.validate.side_effect = exc

        with pytest.raises(AnsibleError, match=r'throwaway msg'):
            vault_list_lookup.run(terms='fake', variables=minimal_vars)

    @pytest.mark.parametrize('paths', [['fake1'], ['fake2', 'fake3']])
    def test_vault_list_return_data(self, vault_list_lookup, minimal_vars, list_response, vault_client, paths):
        client = vault_client

        expected_calls = [mock.call(p) for p in paths]

        def _fake_list_operation(path):
            r = list_response.copy()
            r.update({'_path': path})
            return r

        client.list = mock.Mock(wraps=_fake_list_operation)

        response = vault_list_lookup.run(terms=paths, variables=minimal_vars)

        client.list.assert_has_calls(expected_calls)

        assert len(response) == len(paths), "%i paths processed but got %i responses" % (len(paths), len(response))

        for p in paths:
            r = response.pop(0)
            ins_p = r.pop('_path')
            assert p == ins_p, "expected '_path=%s' field was not found in response, got %r" % (p, ins_p)
