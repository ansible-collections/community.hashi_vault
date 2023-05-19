# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from re import escape as re_escape

from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.plugins.lookup import LookupBase

from ......plugins.plugin_utils._hashi_vault_plugin import HashiVaultPlugin
from ......plugins.plugin_utils._hashi_vault_lookup_base import HashiVaultLookupBase


@pytest.fixture
def hashi_vault_lookup_module():
    return FakeLookupModule()


class FakeLookupModule(HashiVaultLookupBase):
    def run(self, terms, variables=None, **kwargs):
        pass


class TestHashiVaultLookupBase(object):

    def test_is_hashi_vault_plugin(self, hashi_vault_lookup_module):
        assert issubclass(type(hashi_vault_lookup_module), HashiVaultPlugin)

    def test_is_ansible_lookup_base(self, hashi_vault_lookup_module):
        assert issubclass(type(hashi_vault_lookup_module), LookupBase)
        hashi_vault_lookup_module.run([])  # run this for "coverage"

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
