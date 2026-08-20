# -*- coding: utf-8 -*-
# Copyright (c) 2022 Brian Scholer (@briantist)
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
def vault_read_lookup():
    return lookup_loader.get('community.hashi_vault.vault_read')


@pytest.fixture
def kv1_get_response(fixture_loader):
    return fixture_loader('kv1_get_response.json')


class TestVaultReadLookup(object):

    def test_vault_read_is_lookup_base(self, vault_read_lookup):
        assert issubclass(type(vault_read_lookup), HashiVaultLookupBase)

    @pytest.mark.parametrize('exc', [HashiVaultValueError('throwaway msg'), NotImplementedError('throwaway msg')])
    def test_vault_read_authentication_error(self, vault_read_lookup, minimal_vars, authenticator, exc):
        authenticator.authenticate.side_effect = exc

        with pytest.raises(AnsibleError, match=r'throwaway msg'):
            vault_read_lookup.run(terms='fake', variables=minimal_vars)

    @pytest.mark.parametrize('exc', [HashiVaultValueError('throwaway msg'), NotImplementedError('throwaway msg')])
    def test_vault_read_auth_validation_error(self, vault_read_lookup, minimal_vars, authenticator, exc):
        authenticator.validate.side_effect = exc

        with pytest.raises(AnsibleError, match=r'throwaway msg'):
            vault_read_lookup.run(terms='fake', variables=minimal_vars)

    @pytest.mark.parametrize('paths', [['fake1'], ['fake2', 'fake3']])
    def test_vault_read_return_data(self, vault_read_lookup, minimal_vars, kv1_get_response, vault_client, paths):
        client = vault_client

        expected_calls = [mock.call(p) for p in paths]

        def _fake_kv1_get(path):
            r = kv1_get_response.copy()
            r.update({'_path': path})
            return r

        client.read = mock.Mock(wraps=_fake_kv1_get)

        response = vault_read_lookup.run(terms=paths, variables=minimal_vars)

        client.read.assert_has_calls(expected_calls)

        assert len(response) == len(paths), "%i paths processed but got %i responses" % (len(paths), len(response))

        for p in paths:
            r = response.pop(0)
            ins_p = r.pop('_path')
            assert p == ins_p, "expected '_path=%s' field was not found in response, got %r" % (p, ins_p)
