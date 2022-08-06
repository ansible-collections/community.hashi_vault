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

from .....plugins.lookup import vault_kv1_get


hvac = pytest.importorskip('hvac')


pytestmark = pytest.mark.usefixtures(
    'patch_authenticator',
    'patch_get_vault_client',
)


@pytest.fixture
def vault_kv1_get_lookup():
    return lookup_loader.get('community.hashi_vault.vault_kv1_get')


@pytest.fixture
def kv1_get_response(fixture_loader):
    return fixture_loader('kv1_get_response.json')


class TestVaultKv1GetLookup(object):

    def test_vault_kv1_get_is_lookup_base(self, vault_kv1_get_lookup):
        assert issubclass(type(vault_kv1_get_lookup), HashiVaultLookupBase)

    def test_vault_kv1_get_no_hvac(self, vault_kv1_get_lookup, minimal_vars):
        with mock.patch.object(vault_kv1_get, 'HVAC_IMPORT_ERROR', new=ImportError()):
            with pytest.raises(AnsibleError, match=r"This plugin requires the 'hvac' Python library"):
                vault_kv1_get_lookup.run(terms='fake', variables=minimal_vars)

    @pytest.mark.parametrize('exc', [HashiVaultValueError('throwaway msg'), NotImplementedError('throwaway msg')])
    def test_vault_kv1_get_authentication_error(self, vault_kv1_get_lookup, minimal_vars, authenticator, exc):
        authenticator.authenticate.side_effect = exc

        with pytest.raises(AnsibleError, match=r'throwaway msg'):
            vault_kv1_get_lookup.run(terms='fake', variables=minimal_vars)

    @pytest.mark.parametrize('exc', [HashiVaultValueError('throwaway msg'), NotImplementedError('throwaway msg')])
    def test_vault_kv1_get_auth_validation_error(self, vault_kv1_get_lookup, minimal_vars, authenticator, exc):
        authenticator.validate.side_effect = exc

        with pytest.raises(AnsibleError, match=r'throwaway msg'):
            vault_kv1_get_lookup.run(terms='fake', variables=minimal_vars)

    @pytest.mark.parametrize('paths', [['fake1'], ['fake2', 'fake3']])
    @pytest.mark.parametrize('engine_mount_point', ['kv', 'other'])
    def test_vault_kv1_get_return_data(self, vault_kv1_get_lookup, minimal_vars, kv1_get_response, vault_client, paths, engine_mount_point):
        client = vault_client

        expected_calls = [mock.call(path=p, mount_point=engine_mount_point) for p in paths]

        expected = {}
        expected['raw'] = kv1_get_response.copy()
        expected['metadata'] = kv1_get_response.copy()
        expected['data'] = expected['metadata'].pop('data')
        expected['secret'] = expected['data']

        def _fake_kv1_get(path, mount_point):
            r = kv1_get_response.copy()
            r['data'] = r['data'].copy()
            r['data'].update({'_path': path})
            r['data'].update({'_mount': mount_point})
            return r

        client.secrets.kv.v1.read_secret = mock.Mock(wraps=_fake_kv1_get)

        response = vault_kv1_get_lookup.run(terms=paths, variables=minimal_vars, engine_mount_point=engine_mount_point)

        client.secrets.kv.v1.read_secret.assert_has_calls(expected_calls)

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
                "Invalid path for a versioned K/V secrets engine",
                r"^Invalid path for a versioned K/V secrets engine \['[^']+'\]. If this is a KV version 2 path, use community.hashi_vault.vault_kv2_get"
            ),
            (hvac.exceptions.InvalidPath, "", r"^Invalid or missing path \['[^']+'\]"),
        ]
    )
    @pytest.mark.parametrize('path', ['path/1', 'second/path'])
    def test_vault_kv1_get_exceptions(self, vault_kv1_get_lookup, minimal_vars, vault_client, path, exc):
        client = vault_client

        client.secrets.kv.v1.read_secret.side_effect = exc[0](exc[1])

        with pytest.raises(AnsibleError) as e:
            vault_kv1_get_lookup.run(terms=[path], variables=minimal_vars)

        match = re.search(exc[2], str(e.value))

        assert match is not None, "result: %r\ndid not match: %s" % (e.value, exc[2])

        try:
            assert path == match.group(1), "expected: %s\ngot: %s" % (match.group(1), path)
        except IndexError:
            pass
