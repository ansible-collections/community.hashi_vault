# -*- coding: utf-8 -*-
# Copyright (c) 2022 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import json

from ...compat import mock

from .....plugins.modules import vault_pki_generate_certificate
from .....plugins.module_utils._hashi_vault_common import HashiVaultValueError
from .....plugins.module_utils._authenticator import HashiVaultAuthenticator


pytestmark = pytest.mark.usefixtures(
    'patch_ansible_module',
    'patch_authenticator',
    'patch_get_vault_client',
)


@pytest.fixture
def failed_authenticator():
    authenticator = HashiVaultAuthenticator
    authenticator.validate = mock.Mock(side_effect=HashiVaultValueError("Authentication failed"))
    authenticator.authenticate = mock.Mock()

    return authenticator


@pytest.fixture
def patch_failed_authenticator(failed_authenticator):
    with mock.patch(
            'ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_module.HashiVaultAuthenticator',
            new=failed_authenticator):
        yield


def _connection_options():
    return {
        'auth_method': 'token',
        'url': 'http://myvault',
        'token': 'throwaway',
    }


def _sample_options():
    return {
        'role_name': 'some_role',
        'common_name': 'common_name',
        'alt_names': ['a', 'b'],
        'ip_sans': ['c', 'd'],
        'uri_sans': ['e', 'f'],
        'other_sans': ['g', 'h'],
        'ttl': '1h',
        'format': 'der',
        'private_key_format': 'pkcs8',
        'exclude_cn_from_sans': True,
        'engine_mount_point': 'alt',
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
def translated_options(sample_options):
    toplevel = {
        'role_name': 'name',
        'engine_mount_point': 'mount_point',
        'common_name': 'common_name',
    }

    opt = {'extra_params': {}}
    for k, v in sample_options.items():
        if k in toplevel:
            opt[toplevel[k]] = v
        else:
            if isinstance(v, list):
                val = ','.join(v)
            else:
                val = v

            opt['extra_params'][k] = val

    return opt


@pytest.fixture
def pki_generate_certificate_response(fixture_loader):
    return fixture_loader('pki_generate_certificate_response.json')


class TestModuleVaultPkiGenerateCertificate():

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options()], indirect=True)
    def test_vault_pki_generate_certificate_options(self, pki_generate_certificate_response, translated_options, vault_client, capfd):
        client = vault_client
        client.secrets.pki.generate_certificate.return_value = pki_generate_certificate_response

        with pytest.raises(SystemExit) as e:
            vault_pki_generate_certificate.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        client.secrets.pki.generate_certificate.assert_called_once_with(**translated_options)

        assert result['data'] == pki_generate_certificate_response, (
            "module result did not match expected result:\nmodule: %r\nexpected: %r" % (result['data'], pki_generate_certificate_response)
        )
        assert e.value.code == 0

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options()], indirect=True)
    def test_vault_pki_generate_certificate_vault_exception(self, vault_client, capfd):
        hvac = pytest.importorskip('hvac')

        client = vault_client
        client.secrets.pki.generate_certificate.side_effect = hvac.exceptions.VaultError

        with pytest.raises(SystemExit) as e:
            vault_pki_generate_certificate.main()

        assert e.value.code != 0

    @pytest.mark.parametrize('patch_ansible_module', [_combined_options()], indirect=True)
    def test_vault_pki_generate_certificate_authenticator_exception(self, pki_generate_certificate_response, patch_failed_authenticator, vault_client, capfd):
        client = vault_client
        client.secrets.pki.generate_certificate.return_value = pki_generate_certificate_response

        with pytest.raises(SystemExit) as e:
            vault_pki_generate_certificate.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert 'msg' in result, "'msg' not found in module output"

        assert result['msg'] == 'Authentication failed', (
            f"Expected msg to be 'Authentication failed', got '{result['msg']}'"
        )

        assert e.value.code != 0, "Expected non-zero exit code when authentication fails"
