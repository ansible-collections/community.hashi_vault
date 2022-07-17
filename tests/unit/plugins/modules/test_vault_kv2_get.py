# -*- coding: utf-8 -*-
# Copyright (c) 2022 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import re
import json

from ansible.module_utils.basic import missing_required_lib

from ...compat import mock
from .....plugins.modules import vault_kv2_get
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
        'engine_mount_point': 'secret',
        'path': 'endpoint',
    }


def _combined_options(**kwargs):
    opt = _connection_options()
    opt.update(_sample_options())
    opt.update(kwargs)
    return opt


@pytest.fixture
def kv2_get_response(fixture_loader):
    return fixture_loader('kv2_get_response.json')


class TestModuleVaultKv2Get():

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options()], indirect=True)
    @pytest.mark.parametrize('exc', [HashiVaultValueError('throwaway msg'), NotImplementedError('throwaway msg')])
    def test_vault_kv2_get_authentication_error(self, authenticator, exc, capfd):
        authenticator.authenticate.side_effect = exc

        with pytest.raises(SystemExit) as e:
            vault_kv2_get.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)
        assert result['msg'] == 'throwaway msg', "result: %r" % result

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options()], indirect=True)
    @pytest.mark.parametrize('exc', [HashiVaultValueError('throwaway msg'), NotImplementedError('throwaway msg')])
    def test_vault_kv2_get_auth_validation_error(self, authenticator, exc, capfd):
        authenticator.validate.side_effect = exc

        with pytest.raises(SystemExit) as e:
            vault_kv2_get.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)
        assert result['msg'] == 'throwaway msg'

    @pytest.mark.parametrize('opt_engine_mount_point', ['secret', 'other'])
    @pytest.mark.parametrize('opt_version', [None, 2, 10])
    @pytest.mark.parametrize('patch_ansible_module', [[_combined_options(), 'engine_mount_point', 'version']], indirect=True)
    def test_vault_kv2_get_return_data(self, patch_ansible_module, kv2_get_response, vault_client, opt_engine_mount_point, opt_version, capfd):
        client = vault_client
        rv = kv2_get_response.copy()
        rv['data']['metadata']['version'] = opt_version
        client.secrets.kv.v2.read_secret_version.return_value = rv

        expected = {}
        expected['raw'] = rv.copy()
        expected['metadata'] = expected['raw']['data']['metadata']
        expected['data'] = expected['raw']['data']
        expected['secret'] = expected['data']['data']

        with pytest.raises(SystemExit) as e:
            vault_kv2_get.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code == 0, "result: %r" % (result,)

        client.secrets.kv.v2.read_secret_version.assert_called_once_with(
            path=patch_ansible_module['path'],
            mount_point=patch_ansible_module['engine_mount_point'],
            version=opt_version
        )

        for k, v in expected.items():
            assert result[k] == v, (
                "module result did not match expected result:\nmodule: %r\nkey: %s\nexpected: %r" % (result[k], k, v)
            )

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options()], indirect=True)
    def test_vault_kv2_get_no_hvac(self, capfd):
        with mock.patch.multiple(vault_kv2_get, HAS_HVAC=False, HVAC_IMPORT_ERROR=None, create=True):
            with pytest.raises(SystemExit) as e:
                vault_kv2_get.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)
        assert result['msg'] == missing_required_lib('hvac')

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
    @pytest.mark.parametrize('patch_ansible_module', [[_combined_options(), 'path', 'version']], indirect=True)
    @pytest.mark.parametrize('opt_path', ['path/1', 'second/path'])
    @pytest.mark.parametrize('opt_version', [None, 2, 10])
    def test_vault_kv2_get_vault_exception(self, vault_client, exc, opt_version, opt_path, capfd):

        client = vault_client
        client.secrets.kv.v2.read_secret_version.side_effect = exc[0](exc[1])

        with pytest.raises(SystemExit) as e:
            vault_kv2_get.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)
        match = re.search(exc[2], result['msg'])
        assert match is not None, "result: %r\ndid not match: %s" % (result, exc[2])

        assert opt_path == match.group(1)

        try:
            assert (opt_version is None) == (match.group(2) == 'latest')
            assert (opt_version is not None) == (match.group(2) == str(opt_version))
        except IndexError:
            pass
