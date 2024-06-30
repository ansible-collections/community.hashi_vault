# -*- coding: utf-8 -*-
# Copyright (c) 2022 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import re
import json

from .....plugins.modules import vault_write
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


@pytest.fixture
def approle_secret_id_write_response(fixture_loader):
    return fixture_loader('approle_secret_id_write_response.json')


class TestModuleVaultWrite():

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options()], indirect=True)
    @pytest.mark.parametrize('exc', [HashiVaultValueError('throwaway msg'), NotImplementedError('throwaway msg')])
    def test_vault_write_authentication_error(self, authenticator, exc, capfd):
        authenticator.authenticate.side_effect = exc

        with pytest.raises(SystemExit) as e:
            vault_write.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)
        assert result['msg'] == 'throwaway msg', "result: %r" % result

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options()], indirect=True)
    @pytest.mark.parametrize('exc', [HashiVaultValueError('throwaway msg'), NotImplementedError('throwaway msg')])
    def test_vault_write_auth_validation_error(self, authenticator, exc, capfd):
        authenticator.validate.side_effect = exc

        with pytest.raises(SystemExit) as e:
            vault_write.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)
        assert result['msg'] == 'throwaway msg'

    @pytest.mark.parametrize('opt_data', [{}, {'thing': 'one', 'thang': 'two'}])
    @pytest.mark.parametrize('opt_wrap_ttl', [None, '5m'])
    @pytest.mark.parametrize('patch_ansible_module', [[_combined_options(), 'data', 'wrap_ttl']], indirect=True)
    def test_vault_write_return_data(self, patch_ansible_module, approle_secret_id_write_response, vault_client, opt_wrap_ttl, opt_data, capfd):
        client = vault_client
        client.write_data.return_value = approle_secret_id_write_response

        with pytest.raises(SystemExit) as e:
            vault_write.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code == 0, "result: %r" % (result,)

        client.write_data.assert_called_once_with(path=patch_ansible_module['path'], wrap_ttl=opt_wrap_ttl, data=opt_data)

        assert result['data'] == approle_secret_id_write_response, (
            "module result did not match expected result:\nmodule: %r\nexpected: %r" % (result['data'], approle_secret_id_write_response)
        )

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options()], indirect=True)
    def test_vault_write_empty_response(self, vault_client, requests_unparseable_response, capfd):
        client = vault_client

        requests_unparseable_response.status_code = 204

        client.write_data.return_value = requests_unparseable_response

        with pytest.raises(SystemExit) as e:
            vault_write.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code == 0, "result: %r" % (result,)

        assert result['data'] == {}

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options()], indirect=True)
    def test_vault_write_unparseable_response(self, vault_client, requests_unparseable_response, module_warn, capfd):
        client = vault_client

        requests_unparseable_response.status_code = 200
        requests_unparseable_response.content = '﷽'

        client.write_data.return_value = requests_unparseable_response

        with pytest.raises(SystemExit) as e:
            vault_write.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code == 0, "result: %r" % (result,)
        assert result['data'] == '﷽'

        module_warn.assert_called_once_with('Vault returned status code 200 and an unparsable body.')

    @pytest.mark.parametrize(
        'exc',
        [
            (hvac.exceptions.Forbidden, r'^Forbidden: Permission Denied to path'),
            (hvac.exceptions.InvalidPath, r"^The path '[^']+' doesn't seem to exist"),
            (hvac.exceptions.InternalServerError, r'^Internal Server Error:'),
        ]
    )
    @pytest.mark.parametrize('patch_ansible_module', [_combined_options()], indirect=True)
    def test_vault_write_vault_exception(self, vault_client, exc, capfd):

        client = vault_client
        client.write_data.side_effect = exc[0]

        with pytest.raises(SystemExit) as e:
            vault_write.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)
        assert re.search(exc[1], result['msg']) is not None

    @pytest.mark.parametrize(
        'opt_data',
        [
            {"path": 'path_value'},
            {"wrap_ttl": 'wrap_ttl_value'},
            {"path": 'data_value', "wrap_ttl": 'write_ttl_value'},
        ],
    )
    @pytest.mark.parametrize('patch_ansible_module', [[_combined_options(), 'data']], indirect=True)
    def test_vault_write_data_fallback_bad_params(self, vault_client, opt_data, capfd):
        client = vault_client
        client.mock_add_spec(['write'])

        with pytest.raises(SystemExit) as e:
            vault_write.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)
        assert re.search(r"To use 'path' or 'wrap_ttl' as data keys, use hvac >= 1\.2", result['msg']) is not None

        client.write.assert_not_called()

    @pytest.mark.parametrize(
        'opt_data',
        [
            {"item1": 'item1_value'},
            {"item2": 'item2_value'},
            {"item1": 'item1_value', "item2": 'item2_value'},
        ],
    )
    @pytest.mark.parametrize('patch_ansible_module', [[_combined_options(), 'data']], indirect=True)
    def test_vault_write_data_fallback_write(self, vault_client, opt_data, patch_ansible_module, approle_secret_id_write_response, capfd):
        client = vault_client
        client.mock_add_spec(['write'])
        client.write.return_value = approle_secret_id_write_response

        with pytest.raises(SystemExit) as e:
            vault_write.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code == 0, "result: %r" % (result,)

        client.write.assert_called_once_with(path=patch_ansible_module['path'], wrap_ttl=None, **opt_data)
