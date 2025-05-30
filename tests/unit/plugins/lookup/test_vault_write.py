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

# needs to be a relative import otherwise it breaks test_vault_write_unparseable_response.
from .....plugins.lookup import vault_write  # pylint: disable=unused-import


hvac = pytest.importorskip('hvac')


pytestmark = pytest.mark.usefixtures(
    'patch_authenticator',
    'patch_get_vault_client',
)


@pytest.fixture
def vault_write_lookup():
    return lookup_loader.get('community.hashi_vault.vault_write')


@pytest.fixture
def approle_secret_id_write_response(fixture_loader):
    return fixture_loader('approle_secret_id_write_response.json')


class TestVaultWriteLookup(object):

    def test_vault_write_is_lookup_base(self, vault_write_lookup):
        assert issubclass(type(vault_write_lookup), HashiVaultLookupBase)

    @pytest.mark.parametrize('exc', [HashiVaultValueError('throwaway msg'), NotImplementedError('throwaway msg')])
    def test_vault_write_authentication_error(self, vault_write_lookup, minimal_vars, authenticator, exc):
        authenticator.authenticate.side_effect = exc

        with pytest.raises(AnsibleError, match=r'throwaway msg'):
            vault_write_lookup.run(terms='fake', variables=minimal_vars)

    @pytest.mark.parametrize('exc', [HashiVaultValueError('throwaway msg'), NotImplementedError('throwaway msg')])
    def test_vault_write_auth_validation_error(self, vault_write_lookup, minimal_vars, authenticator, exc):
        authenticator.validate.side_effect = exc

        with pytest.raises(AnsibleError, match=r'throwaway msg'):
            vault_write_lookup.run(terms='fake', variables=minimal_vars)

    @pytest.mark.parametrize('paths', [['fake1'], ['fake2', 'fake3']])
    @pytest.mark.parametrize('data', [{}, {'a': 1, 'b': 'two'}])
    @pytest.mark.parametrize('wrap_ttl', [None, '5m'])
    def test_vault_write_return_data(self, vault_write_lookup, minimal_vars, approle_secret_id_write_response, vault_client, paths, data, wrap_ttl):
        client = vault_client

        expected_calls = [mock.call(path=p, wrap_ttl=wrap_ttl, data=data) for p in paths]

        def _fake_write(path, wrap_ttl, data=None):
            r = approle_secret_id_write_response.copy()
            r.update({'path': path})
            return r

        client.write_data = mock.Mock(wraps=_fake_write)

        response = vault_write_lookup.run(terms=paths, variables=minimal_vars, wrap_ttl=wrap_ttl, data=data)

        client.write_data.assert_has_calls(expected_calls)

        assert len(response) == len(paths), "%i paths processed but got %i responses" % (len(paths), len(response))

        for p in paths:
            r = response.pop(0)
            m = r.pop('path')
            assert p == m, "expected 'path=%s' field was not found in response, got %r" % (p, m)
            assert r == approle_secret_id_write_response, (
                "remaining response did not match expected\nresponse: %r\nexpected: %r" % (r, approle_secret_id_write_response)
            )

    def test_vault_write_empty_response(self, vault_write_lookup, minimal_vars, vault_client, requests_unparseable_response):
        client = vault_client

        requests_unparseable_response.status_code = 204

        client.write_data.return_value = requests_unparseable_response

        response = vault_write_lookup.run(terms=['fake'], variables=minimal_vars)

        assert response[0] == {}

    def test_vault_write_unparseable_response(self, vault_write_lookup, minimal_vars, vault_client, requests_unparseable_response):
        client = vault_client

        requests_unparseable_response.status_code = 200
        requests_unparseable_response.content = '﷽'

        client.write_data.return_value = requests_unparseable_response

        with mock.patch('ansible_collections.community.hashi_vault.plugins.lookup.vault_write.display.warning') as warning:
            response = vault_write_lookup.run(terms=['fake'], variables=minimal_vars)
            warning.assert_called_once_with('Vault returned status code 200 and an unparsable body.')

        assert response[0] == '﷽'

    @pytest.mark.parametrize(
        'exc',
        [
            (hvac.exceptions.Forbidden, r'^Forbidden: Permission Denied to path'),
            (hvac.exceptions.InvalidPath, r"^The path '[^']+' doesn't seem to exist"),
            (hvac.exceptions.InternalServerError, r'^Internal Server Error:'),
        ]
    )
    def test_vault_write_exceptions(self, vault_write_lookup, minimal_vars, vault_client, exc):
        client = vault_client

        client.write_data.side_effect = exc[0]

        with pytest.raises(AnsibleError, match=exc[1]):
            vault_write_lookup.run(terms=['fake'], variables=minimal_vars)

    @pytest.mark.parametrize(
        'data',
        [
            {"path": mock.sentinel.path_value},
            {"wrap_ttl": mock.sentinel.wrap_ttl_value},
            {"path": mock.sentinel.data_value, "wrap_ttl": mock.sentinel.write_ttl_value},
        ],
    )
    def test_vault_write_data_fallback_bad_params(self, vault_write_lookup, minimal_vars, vault_client, data):
        client = vault_client
        client.mock_add_spec(['write'])

        with pytest.raises(AnsibleError, match=r"To use 'path' or 'wrap_ttl' as data keys, use hvac >= 1\.2"):
            vault_write_lookup.run(terms=['fake'], variables=minimal_vars, data=data)

        client.write.assert_not_called()

    @pytest.mark.parametrize(
        'data',
        [
            {"item1": mock.sentinel.item1_value},
            {"item2": mock.sentinel.item2_value},
            {"item1": mock.sentinel.item1_value, "item2": mock.sentinel.item2_value},
        ],
    )
    def test_vault_write_data_fallback_write(self, vault_write_lookup, minimal_vars, vault_client, data):
        client = vault_client
        client.mock_add_spec(['write'])

        vault_write_lookup.run(terms=['fake'], variables=minimal_vars, data=data)

        client.write.assert_called_once_with(path='fake', wrap_ttl=None, **data)
