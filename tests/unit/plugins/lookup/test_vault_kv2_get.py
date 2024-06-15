# -*- coding: utf-8 -*-
# Copyright (c) 2022 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re
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
def vault_kv2_get_lookup():
    return lookup_loader.get('community.hashi_vault.vault_kv2_get')


@pytest.fixture
def kv2_get_response(fixture_loader):
    return fixture_loader('kv2_get_response.json')


class TestVaultKv2GetLookup(object):

    def test_vault_kv2_get_is_lookup_base(self, vault_kv2_get_lookup):
        assert issubclass(type(vault_kv2_get_lookup), HashiVaultLookupBase)

    @pytest.mark.parametrize('exc', [HashiVaultValueError('throwaway msg'), NotImplementedError('throwaway msg')])
    def test_vault_kv2_get_authentication_error(self, vault_kv2_get_lookup, minimal_vars, authenticator, exc):
        authenticator.authenticate.side_effect = exc

        with pytest.raises(AnsibleError, match=r'throwaway msg'):
            vault_kv2_get_lookup.run(terms='fake', variables=minimal_vars)

    @pytest.mark.parametrize('exc', [HashiVaultValueError('throwaway msg'), NotImplementedError('throwaway msg')])
    def test_vault_kv2_get_auth_validation_error(self, vault_kv2_get_lookup, minimal_vars, authenticator, exc):
        authenticator.validate.side_effect = exc

        with pytest.raises(AnsibleError, match=r'throwaway msg'):
            vault_kv2_get_lookup.run(terms='fake', variables=minimal_vars)

    @pytest.mark.parametrize('paths', [['fake1'], ['fake2', 'fake3']])
    @pytest.mark.parametrize('engine_mount_point', ['secret', 'other'])
    @pytest.mark.parametrize('version', [None, 2, 10])
    def test_vault_kv2_get_return_data(self, vault_kv2_get_lookup, minimal_vars, kv2_get_response, vault_client, paths, engine_mount_point, version):
        client = vault_client
        rv = kv2_get_response.copy()
        rv['data']['metadata']['version'] = version

        expected = {}
        expected['raw'] = rv.copy()
        expected['metadata'] = expected['raw']['data']['metadata']
        expected['data'] = expected['raw']['data']
        expected['secret'] = expected['data']['data']

        expected_calls = [mock.call(path=p, version=version, mount_point=engine_mount_point) for p in paths]

        def _fake_kv2_get(path, version, mount_point):
            r = rv.copy()
            r['data']['data'] = r['data']['data'].copy()
            r['data']['data'].update({'_path': path})
            r['data']['data'].update({'_mount': mount_point})
            return r

        client.secrets.kv.v2.read_secret_version = mock.Mock(wraps=_fake_kv2_get)

        response = vault_kv2_get_lookup.run(terms=paths, variables=minimal_vars, version=version, engine_mount_point=engine_mount_point)

        client.secrets.kv.v2.read_secret_version.assert_has_calls(expected_calls)

        assert len(response) == len(paths), "%i paths processed but got %i responses" % (len(paths), len(response))

        for p in paths:
            r = response.pop(0)
            ins_p = r['secret'].pop('_path')
            ins_m = r['secret'].pop('_mount')
            assert p == ins_p, "expected '_path=%s' field was not found in response, got %r" % (p, ins_p)
            assert engine_mount_point == ins_m, "expected '_mount=%s' field was not found in response, got %r" % (engine_mount_point, ins_m)
            assert r['raw'] == expected['raw'], (
                "remaining response did not match expected\nresponse: %r\nexpected: %r" % (r, expected['raw'])
            )
            assert r['metadata'] == expected['metadata']
            assert r['data'] == expected['data']
            assert r['secret'] == expected['secret']

    @pytest.mark.parametrize(
        'exc',
        [
            (hvac.exceptions.Forbidden, "", r"^Forbidden: Permission Denied to path \['([^']+)'\]"),
            (
                hvac.exceptions.InvalidPath,
                "",
                r"^Invalid or missing path \['([^']+)'\] with secret version '(\d+|latest)'. Check the path or secret version"
            ),
        ]
    )
    @pytest.mark.parametrize('path', ['path/1', 'second/path'])
    @pytest.mark.parametrize('version', [None, 2, 10])
    def test_vault_kv2_get_exceptions(self, vault_kv2_get_lookup, minimal_vars, vault_client, path, version, exc):
        client = vault_client

        client.secrets.kv.v2.read_secret_version.side_effect = exc[0](exc[1])

        with pytest.raises(AnsibleError) as e:
            vault_kv2_get_lookup.run(terms=[path], variables=minimal_vars, version=version)

        match = re.search(exc[2], str(e.value))

        assert path == match.group(1), "expected: %s\ngot: %s" % (match.group(1), path)

        try:
            assert (version is None) == (match.group(2) == 'latest')
            assert (version is not None) == (match.group(2) == str(version))
        except IndexError:
            pass
