# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import pytest

from ansible import constants as C
from ansible.config.manager import ConfigManager
from ansible.plugins.loader import lookup_loader

from urllib.parse import urlparse

from ansible_collections.community.hashi_vault.tests.unit.compat import mock

from ansible_collections.community.hashi_vault.plugins.plugin_utils._hashi_vault_lookup_base import HashiVaultLookupBase

from requests.exceptions import ConnectionError


@pytest.fixture
def hashi_vault_lookup_module():
    return lookup_loader.get('community.hashi_vault.hashi_vault')


class TestHashiVaultLookup(object):

    def test_is_hashi_vault_lookup_base(self, hashi_vault_lookup_module):
        assert issubclass(type(hashi_vault_lookup_module), HashiVaultLookupBase)

    @pytest.mark.parametrize(
        'ini_value,variables,direct,skip_verify,expected',
        [
            (None, {}, {}, None, True),
            ('false', {}, {}, None, False),
            ('true', {}, {}, None, True),
            ('false', {'ansible_hashi_vault_validate_certs': True}, {}, None, True),
            ('true', {'ansible_hashi_vault_validate_certs': False}, {}, None, False),
            ('false', {}, {'validate_certs': True}, None, True),
            ('true', {}, {'validate_certs': False}, None, False),
            ('true', {}, {}, 'true', True),
            ('false', {}, {}, 'false', False),
            (None, {}, {}, 'true', False),
        ],
    )
    def test_validate_certs_ini(
        self, hashi_vault_lookup_module, tmp_path, monkeypatch,
        ini_value, variables, direct, skip_verify, expected,
    ):
        config_file = tmp_path / 'ansible.cfg'
        config_file.write_text('[hashi_vault_collection]\n' + (
            '' if ini_value is None else 'validate_certs = %s\n' % ini_value
        ))
        plugin_name = hashi_vault_lookup_module._load_name
        definitions = C.config.get_configuration_definitions('lookup', plugin_name)
        config = ConfigManager(conf_file=str(config_file))
        config.initialize_plugin_configuration_definitions('lookup', plugin_name, definitions)
        monkeypatch.setattr(C, 'config', config)
        monkeypatch.delenv('VAULT_CACERT', raising=False)
        monkeypatch.delenv('VAULT_SKIP_VERIFY', raising=False)
        if skip_verify is not None:
            monkeypatch.setenv('VAULT_SKIP_VERIFY', skip_verify)

        options = dict(url='https://vault.example', secret='secret/test')
        options.update(direct)
        hashi_vault_lookup_module.set_options(var_options=variables, direct=options)
        hashi_vault_lookup_module.connection_options.process_connection_options()

        assert hashi_vault_lookup_module.connection_options.get_hvac_connection_options()['verify'] is expected

    # TODO: this test should be decoupled from the hashi_vault lookup and moved to the connection options tests
    @pytest.mark.parametrize(
        'envpatch,expected',
        [
            ({'VAULT_ADDR': 'http://vault:0'}, 'http://vault:0'),
            ({'ANSIBLE_HASHI_VAULT_ADDR': 'https://vaultalt'}, 'https://vaultalt'),
            ({'VAULT_ADDR': 'https://vaultlow:8443', 'ANSIBLE_HASHI_VAULT_ADDR': 'http://vaulthigh:8200'}, 'http://vaulthigh:8200'),
        ],
    )
    def test_vault_addr_low_pref(self, hashi_vault_lookup_module, envpatch, expected):
        url = urlparse(expected)
        host = url.hostname
        port = url.port if url.port is not None else {'http': 80, 'https': 443}[url.scheme]

        with mock.patch.dict(os.environ, envpatch):
            with pytest.raises(ConnectionError) as e:
                hashi_vault_lookup_module.run(['secret/fake'], token='fake')

        s_err = str(e.value)

        assert str(host) in s_err, "host '%s' not found in exception: %r" % (host, str(e.value))
        assert str(port) in s_err, "port '%i' not found in exception: %r" % (port, str(e.value))
