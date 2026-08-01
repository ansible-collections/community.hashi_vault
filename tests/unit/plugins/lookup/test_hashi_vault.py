# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import pytest

from re import escape as re_escape

from ansible.errors import AnsibleError, AnsibleOptionsError
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

    @pytest.mark.parametrize(
        'term,unqualified',
        [
            ('value1 key2=value2 key3=val_w/=in_it key4=value4', 'key1'),
            ('key1=value1 key2=value2 key3=val_w/=in_it key4=value4', None),
            ('key1=value1 key2=value2 key3=val_w/=in_it key4=value4', 'NotReal'),
        ]
    )
    def test_parse_kev_term_success(self, term, unqualified, hashi_vault_lookup_module):
        EXPECTED = {
            'key1': 'value1',
            'key2': 'value2',
            'key3': 'val_w/=in_it',
            'key4': 'value4',
        }
        parsed = hashi_vault_lookup_module.parse_kev_term(term, plugin_name='fake', first_unqualified=unqualified)

        assert parsed == EXPECTED

    @pytest.mark.parametrize(
        'term,unqualified',
        [
            ('value1 key2=value2 key3=val_w/=in_it key4=value4', None),
            ('key1=value1 value2 key3=val_w/=in_it key4=value4', None),
            ('key1=value1 value2 key3=val_w/=in_it key4=value4', 'key2'),
            ('key1=val1 invalid key3=val3', None),
            ('key1=val1 invalid key3=val3', 'key1'),
        ]
    )
    def test_parse_kev_term_invalid_term_strings(self, term, unqualified, hashi_vault_lookup_module):
        with pytest.raises(AnsibleError):
            parsed = hashi_vault_lookup_module.parse_kev_term(term, plugin_name='fake', first_unqualified=unqualified)

    def test_parse_kev_term_plugin_name_required(self, hashi_vault_lookup_module):
        with pytest.raises(TypeError):
            parsed = hashi_vault_lookup_module.parse_kev_term('key1=value1', first_unqualified='fake')

    @pytest.mark.parametrize('term', [
        'one secret=two a=1 b=2',
        'a=1 secret=one b=2 secret=two',
        'secret=one secret=two a=z b=y',
    ])
    def test_parse_kev_term_duplicate_option(self, term, hashi_vault_lookup_module):
        dup_key = 'secret'
        expected_template = "Duplicate key '%s' in the term string '%s'."
        expected_msg = expected_template % (dup_key, term)
        expected_re = re_escape(expected_msg)
        expected_match = "^%s$" % (expected_re,)

        with pytest.raises(AnsibleOptionsError, match=expected_match):
            hashi_vault_lookup_module.parse_kev_term(term, plugin_name='fake', first_unqualified=dup_key)
