# -*- coding: utf-8 -*-
# Copyright (c) 2023 Tom Kivlin (@tomkivlin)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import re
import json

from .....plugins.modules import vault_list
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
        'path': 'endpoint',
    }


def _combined_options(**kwargs):
    opt = _connection_options()
    opt.update(_sample_options())
    opt.update(kwargs)
    return opt


LIST_FIXTURES = [
    'kv2_list_response.json',
    'policy_list_response.json',
    'userpass_list_response.json',
]


@pytest.fixture(params=LIST_FIXTURES)
def list_response(request, fixture_loader):
    return fixture_loader(request.param)


class TestModuleVaultList():

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options()], indirect=True)
    @pytest.mark.parametrize('exc', [HashiVaultValueError('throwaway msg'), NotImplementedError('throwaway msg')])
    def test_vault_list_authentication_error(self, authenticator, exc, capfd):
        authenticator.authenticate.side_effect = exc

        with pytest.raises(SystemExit) as e:
            vault_list.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)
        assert result['msg'] == 'throwaway msg', "result: %r" % result

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options()], indirect=True)
    @pytest.mark.parametrize('exc', [HashiVaultValueError('throwaway msg'), NotImplementedError('throwaway msg')])
    def test_vault_list_auth_validation_error(self, authenticator, exc, capfd):
        authenticator.validate.side_effect = exc

        with pytest.raises(SystemExit) as e:
            vault_list.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)
        assert result['msg'] == 'throwaway msg'

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options()], indirect=True)
    def test_vault_list_return_data(self, patch_ansible_module, list_response, vault_client, capfd):
        client = vault_client
        client.list.return_value = list_response.copy()

        with pytest.raises(SystemExit) as e:
            vault_list.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code == 0, "result: %r" % (result,)

        client.list.assert_called_once_with(patch_ansible_module['path'])

        assert result['data'] == list_response, "module result did not match expected result:\nexpected: %r\ngot: %r" % (list_response, result)

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options()], indirect=True)
    def test_vault_list_no_data(self, patch_ansible_module, vault_client, capfd):
        client = vault_client
        client.list.return_value = None

        with pytest.raises(SystemExit) as e:
            vault_list.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)

        client.list.assert_called_once_with(patch_ansible_module['path'])

        match = re.search(r"The path '[^']+' doesn't seem to exist", result['msg'])

        assert match is not None, "Unexpected msg: %s" % result['msg']

    @pytest.mark.parametrize(
        'exc',
        [
            (hvac.exceptions.Forbidden, "", r"^Forbidden: Permission Denied to path '([^']+)'"),
        ]
    )
    @pytest.mark.parametrize('patch_ansible_module', [[_combined_options(), 'path']], indirect=True)
    @pytest.mark.parametrize('opt_path', ['path/1', 'second/path'])
    def test_vault_list_vault_exception(self, vault_client, exc, opt_path, capfd):

        client = vault_client
        client.list.side_effect = exc[0](exc[1])

        with pytest.raises(SystemExit) as e:
            vault_list.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)
        match = re.search(exc[2], result['msg'])
        assert match is not None, "result: %r\ndid not match: %s" % (result, exc[2])

        assert opt_path == match.group(1)
