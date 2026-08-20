# -*- coding: utf-8 -*-
# Copyright (c) 2022 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import re
import json

from .....plugins.modules import vault_kv1_get
from .....plugins.module_utils._hashi_vault_common import HashiVaultValueError


hvac = pytest.importorskip('hvac')


pytestmark = pytest.mark.usefixtures(
    'patch_ansible_module',
    'patch_authenticator',
    'patch_get_vault_client',
)


def _connection_options():
    return {
        'auth_method': 'token',
        'url': 'http://myvault',
        'token': 'beep-boop',
    }


def _sample_options():
    return {
        'engine_mount_point': 'kv',
        'path': 'endpoint',
    }


def _combined_options(**kwargs):
    opt = _connection_options()
    opt.update(_sample_options())
    opt.update(kwargs)
    return opt


@pytest.fixture
def kv1_get_response(fixture_loader):
    return fixture_loader('kv1_get_response.json')


class TestModuleVaultKv1Get():

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options()], indirect=True)
    @pytest.mark.parametrize('exc', [HashiVaultValueError('throwaway msg'), NotImplementedError('throwaway msg')])
    def test_vault_kv1_get_authentication_error(self, authenticator, exc, capfd):
        authenticator.authenticate.side_effect = exc

        with pytest.raises(SystemExit) as e:
            vault_kv1_get.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)
        assert result['msg'] == 'throwaway msg', "result: %r" % result

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options()], indirect=True)
    @pytest.mark.parametrize('exc', [HashiVaultValueError('throwaway msg'), NotImplementedError('throwaway msg')])
    def test_vault_kv1_get_auth_validation_error(self, authenticator, exc, capfd):
        authenticator.validate.side_effect = exc

        with pytest.raises(SystemExit) as e:
            vault_kv1_get.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)
        assert result['msg'] == 'throwaway msg'

    @pytest.mark.parametrize('opt_engine_mount_point', ['kv', 'other'])
    @pytest.mark.parametrize('patch_ansible_module', [[_combined_options(), 'engine_mount_point']], indirect=True)
    def test_vault_kv1_get_return_data(self, patch_ansible_module, kv1_get_response, vault_client, opt_engine_mount_point, capfd):
        client = vault_client
        client.secrets.kv.v1.read_secret.return_value = kv1_get_response.copy()

        expected = {}
        expected['raw'] = kv1_get_response.copy()
        expected['metadata'] = kv1_get_response.copy()
        expected['data'] = expected['metadata'].pop('data')
        expected['secret'] = expected['data']

        with pytest.raises(SystemExit) as e:
            vault_kv1_get.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code == 0, "result: %r" % (result,)

        client.secrets.kv.v1.read_secret.assert_called_once_with(path=patch_ansible_module['path'], mount_point=patch_ansible_module['engine_mount_point'])

        for k, v in expected.items():
            assert result[k] == v, (
                "module result did not match expected result:\nmodule: %r\nkey: %s\nexpected: %r" % (result[k], k, v)
            )

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
    @pytest.mark.parametrize('patch_ansible_module', [[_combined_options(), 'path']], indirect=True)
    @pytest.mark.parametrize('opt_path', ['path/1', 'second/path'])
    def test_vault_kv1_get_vault_exception(self, vault_client, exc, opt_path, capfd):

        client = vault_client
        client.secrets.kv.v1.read_secret.side_effect = exc[0](exc[1])

        with pytest.raises(SystemExit) as e:
            vault_kv1_get.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)
        match = re.search(exc[2], result['msg'])
        assert match is not None, "result: %r\ndid not match: %s" % (result, exc[2])

        try:
            assert opt_path == match.group(1)
        except IndexError:
            pass
