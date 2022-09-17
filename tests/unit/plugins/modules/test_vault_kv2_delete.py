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
from .....plugins.modules import vault_kv2_delete
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
def kv2_delete_response():
    class request_response:
        status_code = 204

    return request_response


class TestModuleVaultKv2Delete():

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options()], indirect=True)
    @pytest.mark.parametrize('exc', [HashiVaultValueError('throwaway msg'), NotImplementedError('throwaway msg')])
    def test_vault_kv2_delete_authentication_error(self, authenticator, exc, capfd):
        authenticator.authenticate.side_effect = exc

        with pytest.raises(SystemExit) as e:
            vault_kv2_delete.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)
        assert result['msg'] == 'throwaway msg', "result: %r" % result

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options()], indirect=True)
    @pytest.mark.parametrize('exc', [HashiVaultValueError('throwaway msg'), NotImplementedError('throwaway msg')])
    def test_vault_kv2_get_auth_validation_error(self, authenticator, exc, capfd):
        authenticator.validate.side_effect = exc

        with pytest.raises(SystemExit) as e:
            vault_kv2_delete.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)
        assert result['msg'] == 'throwaway msg'

    @pytest.mark.parametrize('opt_engine_mount_point', ['secret', 'other'])
    @pytest.mark.parametrize('patch_ansible_module', [[_combined_options(), 'engine_mount_point']], indirect=True)
    def test_vault_kv2_delete_return_data(self, patch_ansible_module, kv2_delete_response, vault_client, opt_engine_mount_point, capfd):
        client = vault_client
        client.secrets.kv.v2.delete_latest_version_of_secret.return_value = kv2_delete_response

        expected_response = 204

        with pytest.raises(SystemExit) as e:
            vault_kv2_delete.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code == 0, "result: %r" % (result,)

        client.secrets.kv.v2.delete_latest_version_of_secret.assert_called_once_with(
            path=patch_ansible_module['path'],
            mount_point=patch_ansible_module['engine_mount_point'],
        )

        assert result['response_code'] == expected_response, (
            "module result did not match expected result:\nmodule: %r\nexpected: %r" % (
                result['response_code'], expected_response)
        )

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options()], indirect=True)
    def test_vault_kv2_delete_no_hvac(self, capfd):
        with mock.patch.multiple(vault_kv2_delete, HAS_HVAC=False, HVAC_IMPORT_ERROR=None, create=True):
            with pytest.raises(SystemExit) as e:
                vault_kv2_delete.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)
        assert result['msg'] == missing_required_lib('hvac')

    @pytest.mark.parametrize(
        'exc',
        [
            (hvac.exceptions.Forbidden, "",
             r"^Forbidden: Permission Denied to path \['([^']+)'\]"),
        ]
    )
    @pytest.mark.parametrize('patch_ansible_module', [[_combined_options(), 'path']], indirect=True)
    @pytest.mark.parametrize('opt_path', ['path/1', 'second/path'])
    def test_vault_kv2_get_vault_exception(self, vault_client, exc, opt_path, capfd):

        client = vault_client
        client.secrets.kv.v2.delete_latest_version_of_secret.side_effect = exc[0](
            exc[1])

        with pytest.raises(SystemExit) as e:
            vault_kv2_delete.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)
        match = re.search(exc[2], result['msg'])
        assert match is not None, "result: %r\ndid not match: %s" % (
            result, exc[2])

        assert opt_path == match.group(1)
