# -*- coding: utf-8 -*-
# Copyright (c) 2022 Isaac Wagner (@idwagner)
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
    def test_vault_kv2_delete_auth_validation_error(self, authenticator, exc, capfd):
        authenticator.validate.side_effect = exc

        with pytest.raises(SystemExit) as e:
            vault_kv2_delete.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)
        assert result['msg'] == 'throwaway msg'

    @pytest.mark.parametrize('opt_versions', [None, [1, 3]])
    @pytest.mark.parametrize('patch_ansible_module', [[_combined_options(), 'versions']], indirect=True)
    def test_vault_kv2_delete_empty_response(self, patch_ansible_module, opt_versions, requests_unparseable_response, vault_client, capfd):
        client = vault_client

        requests_unparseable_response.status_code = 204

        if opt_versions:
            client.secrets.kv.v2.delete_secret_versions.return_value = requests_unparseable_response
        else:
            client.secrets.kv.v2.delete_latest_version_of_secret.return_value = requests_unparseable_response

        with pytest.raises(SystemExit) as e:
            vault_kv2_delete.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code == 0, "result: %r" % (result,)

        assert result['data'] == {}

    @pytest.mark.parametrize('opt_versions', [None, [1, 3]])
    @pytest.mark.parametrize('patch_ansible_module', [[_combined_options(), 'versions']], indirect=True)
    def test_vault_kv2_delete_unparseable_response(self, vault_client, opt_versions, requests_unparseable_response, module_warn, capfd):
        client = vault_client

        requests_unparseable_response.status_code = 200
        requests_unparseable_response.content = '(☞ﾟヮﾟ)☞ ┻━┻'

        if opt_versions:
            client.secrets.kv.v2.delete_secret_versions.return_value = requests_unparseable_response
        else:
            client.secrets.kv.v2.delete_latest_version_of_secret.return_value = requests_unparseable_response

        with pytest.raises(SystemExit) as e:
            vault_kv2_delete.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code == 0, "result: %r" % (result,)
        assert result['data'] == '(☞ﾟヮﾟ)☞ ┻━┻'

        module_warn.assert_called_once_with(
            'Vault returned status code 200 and an unparsable body.')

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
    @pytest.mark.parametrize('opt_versions', [None, [1, 3]])
    @pytest.mark.parametrize('opt_path', ['path/1', 'second/path'])
    @pytest.mark.parametrize('patch_ansible_module', [[_combined_options(), 'path', 'versions']], indirect=True)
    def test_vault_kv2_delete_vault_exception(self, vault_client, exc, opt_versions, opt_path, capfd):

        client = vault_client

        if opt_versions:
            client.secrets.kv.v2.delete_secret_versions.side_effect = exc[0](
                exc[1])
        else:
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

    @pytest.mark.parametrize('opt__ansible_check_mode', [False, True])
    @pytest.mark.parametrize('opt_versions', [None])
    @pytest.mark.parametrize('patch_ansible_module', [[
        _combined_options(),
        '_ansible_check_mode',
        'versions'
    ]], indirect=True)
    def test_vault_kv2_delete_latest_version_call(self, vault_client, opt__ansible_check_mode, opt_versions, capfd):

        client = vault_client
        client.secrets.kv.v2.delete_latest_version_of_secret.return_value = {}

        with pytest.raises(SystemExit) as e:
            vault_kv2_delete.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        if opt__ansible_check_mode:
            client.secrets.kv.v2.delete_latest_version_of_secret.assert_not_called()
        else:
            client.secrets.kv.v2.delete_latest_version_of_secret.assert_called_once_with(
                path='endpoint', mount_point='secret')

    @pytest.mark.parametrize('opt__ansible_check_mode', [False, True])
    @pytest.mark.parametrize('opt_versions', [[1, 3]])
    @pytest.mark.parametrize('patch_ansible_module', [[
        _combined_options(),
        '_ansible_check_mode',
        'versions'
    ]], indirect=True)
    def test_vault_kv2_delete_specific_versions_call(self, vault_client, opt__ansible_check_mode, opt_versions, capfd):

        client = vault_client
        client.secrets.kv.v2.delete_secret_versions.return_value = {}

        with pytest.raises(SystemExit) as e:
            vault_kv2_delete.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        if opt__ansible_check_mode:
            client.secrets.kv.v2.delete_secret_versions.assert_not_called()
        else:
            client.secrets.kv.v2.delete_secret_versions.assert_called_once_with(
                path='endpoint', mount_point='secret', versions=[1, 3])
