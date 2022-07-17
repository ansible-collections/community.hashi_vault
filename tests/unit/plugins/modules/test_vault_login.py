# -*- coding: utf-8 -*-
# Copyright (c) 2022 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import json

from ansible.module_utils.basic import missing_required_lib

from ...compat import mock
from .....plugins.modules import vault_login
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
    return {}


def _combined_options(**kwargs):
    opt = _connection_options()
    opt.update(_sample_options())
    opt.update(kwargs)
    return opt


@pytest.fixture
def token_lookup_full_response(fixture_loader):
    return fixture_loader('lookup-self_with_meta.json')


class TestModuleVaultLogin():

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options()], indirect=True)
    @pytest.mark.parametrize('exc', [HashiVaultValueError('throwaway msg'), NotImplementedError('throwaway msg')])
    def test_vault_login_authentication_error(self, authenticator, exc, capfd):
        authenticator.authenticate.side_effect = exc

        with pytest.raises(SystemExit) as e:
            vault_login.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)
        assert result['msg'] == 'throwaway msg', "result: %r" % result

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options()], indirect=True)
    @pytest.mark.parametrize('exc', [HashiVaultValueError('throwaway msg'), NotImplementedError('throwaway msg')])
    def test_vault_login_auth_validation_error(self, authenticator, exc, capfd):
        authenticator.validate.side_effect = exc

        with pytest.raises(SystemExit) as e:
            vault_login.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)
        assert result['msg'] == 'throwaway msg'

    @pytest.mark.parametrize('opt__ansible_check_mode', [False, True])
    @pytest.mark.parametrize(
        ['opt_auth_method', 'opt_token', 'opt_role_id'],
        [
            ('token', 'beep-boop-bloop', None),
            ('approle', None, 'not-used'),
        ]
    )
    @pytest.mark.parametrize('patch_ansible_module', [[
        _combined_options(),
        '_ansible_check_mode',
        'auth_method',
        'token',
        'role_id',
    ]], indirect=True)
    def test_vault_login_return_data(
        self, patch_ansible_module, token_lookup_full_response, authenticator, vault_client,
        opt__ansible_check_mode, opt_auth_method, opt_token, opt_role_id, capfd
    ):
        authenticator.authenticate.return_value = token_lookup_full_response

        with pytest.raises(SystemExit) as e:
            vault_login.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code == 0, "result: %r" % (result,)

        authenticator.validate.assert_called_once()

        assert result['changed'] == (opt_auth_method != 'token')

        if opt__ansible_check_mode:
            authenticator.authenticate.assert_not_called()
            assert result['login'] == {'auth': {'client_token': None}}
        else:
            authenticator.authenticate.assert_called_once_with(vault_client)
            assert result['login'] == token_lookup_full_response, "expected: %r\ngot: %r" % (token_lookup_full_response, result['login'])

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options()], indirect=True)
    def test_vault_login_no_hvac(self, capfd):
        with mock.patch.multiple(vault_login, HAS_HVAC=False, HVAC_IMPORT_ERROR=None, create=True):
            with pytest.raises(SystemExit) as e:
                vault_login.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)
        assert result['msg'] == missing_required_lib('hvac')
