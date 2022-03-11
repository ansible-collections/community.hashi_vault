# -*- coding: utf-8 -*-
# Copyright (c) 2022 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import re
import json

from ansible.module_utils.basic import missing_required_lib

from ...compat import mock
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
        'url': 'http://dummy',
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
def sample_options():
    return _sample_options()


@pytest.fixture
def approle_secret_id_write_response(fixture_loader):
    return fixture_loader('approle_secret_id_write_response.json')


class TestModuleVaultWrite():

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options()], indirect=True)
    @pytest.mark.parametrize('exc', [HashiVaultValueError('dummy msg'), NotImplementedError('dummy msg')])
    def test_vault_write_authentication_error(self, authenticator, exc, capfd):
        authenticator.authenticate.side_effect = exc

        with pytest.raises(SystemExit) as e:
            vault_write.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert result['msg'] == 'dummy msg', "result: %r" % result
        assert e.value.code != 0

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options()], indirect=True)
    @pytest.mark.parametrize('exc', [HashiVaultValueError('dummy msg'), NotImplementedError('dummy msg')])
    def test_vault_write_auth_validation_error(self, authenticator, exc, capfd):
        authenticator.validate.side_effect = exc

        with pytest.raises(SystemExit) as e:
            vault_write.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert result['msg'] == 'dummy msg'
        assert e.value.code != 0

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options(), _combined_options(data={'thing': 'one', 'thang': 'two'})], indirect=True)
    def test_vault_write_return_data(self, patch_ansible_module, approle_secret_id_write_response, vault_client, capfd):
        client = vault_client
        client.write.return_value = approle_secret_id_write_response

        with pytest.raises(SystemExit) as e:
            vault_write.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        client.write.assert_called_once_with(path=patch_ansible_module['path'], **patch_ansible_module.get('data', {}))

        assert result['data'] == approle_secret_id_write_response, (
            "module result did not match expected result:\nmodule: %r\nexpected: %r" % (result['data'], approle_secret_id_write_response)
        )
        assert e.value.code == 0

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options()], indirect=True)
    def test_vault_write_empty_response(self, vault_client, requests_unparseable_response, capfd):
        client = vault_client

        requests_unparseable_response.status_code = 204

        client.write.return_value = requests_unparseable_response

        with pytest.raises(SystemExit) as e:
            vault_write.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert result['data'] == {}

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options()], indirect=True)
    def test_vault_write_unparseable_response(self, vault_client, requests_unparseable_response, module_warn, capfd):
        client = vault_client

        requests_unparseable_response.status_code = 200
        requests_unparseable_response.content = '﷽'

        client.write.return_value = requests_unparseable_response

        with pytest.raises(SystemExit) as e:
            vault_write.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        module_warn.assert_called_once_with('Vault returned status code 200 and an unparsable body.')

        assert result['data'] == '﷽'

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options()], indirect=True)
    def test_vault_write_no_hvac(self, approle_secret_id_write_response, vault_client, capfd):
        client = vault_client
        client.write.return_value = approle_secret_id_write_response

        with mock.patch.multiple(vault_write, HAS_HVAC=False, HVAC_IMPORT_ERROR=None, create=True):
            with pytest.raises(SystemExit) as e:
                vault_write.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert result['msg'] == missing_required_lib('hvac')
        assert e.value.code != 0

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
        client.write.side_effect = exc[0]

        with pytest.raises(SystemExit) as e:
            vault_write.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert re.search(exc[1], result['msg']) is not None
        assert e.value.code != 0
