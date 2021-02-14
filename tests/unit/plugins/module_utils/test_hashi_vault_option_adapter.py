# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
import os
import pytest

from ansible.plugins import AnsiblePlugin
# from ansible.plugins.loader import lookup_loader

from ansible_collections.community.hashi_vault.tests.unit.compat import mock
from ansible_collections.community.hashi_vault.plugins.module_utils.hashi_vault_common import HashiVaultOptionAdapter


SAMPLE_DICT = {
    'key1': 'val1',
    'key2': 2,
    'key3': 'three',
    'key4': 'iiii',
}

SAMPLE_KEYS = sorted(list(SAMPLE_DICT.keys()))

MISSING_KEYS = ['no', 'nein', 'iie']

class FakePlugin(AnsiblePlugin):
    _load_name = 'community.hashi_vault.fake'


class SentinelMarker():
    pass


MARKER = SentinelMarker()

@pytest.fixture()
def sample_dict():
    return SAMPLE_DICT.copy()

@pytest.fixture
def ansible_plugin(sample_dict):
    plugin = FakePlugin()
    plugin._options = sample_dict
    return plugin

@pytest.fixture
def adapter_from_dict(sample_dict):
    return HashiVaultOptionAdapter.from_dict(sample_dict)

@pytest.fixture
def adapter_from_ansible_plugin(ansible_plugin):
    return HashiVaultOptionAdapter.from_ansible_plugin(ansible_plugin)

@pytest.fixture(params=['dict', 'ansible_plugin'])
def adapter(request, adapter_from_dict, adapter_from_ansible_plugin):
    return {
        'dict': adapter_from_dict,
        'ansible_plugin': adapter_from_ansible_plugin,
    }[request.param]

# @pytest.fixture
# def hashi_vault_option_adapter():
#     return HashiVaultHelper()

    #| _getter = None
    #| _setter = None
    #| _haver = None
    #| _updater = None
    #| _getitems = None
    # _getitemsdefault
    #| _defaultsetter = None
    #| _defaultgetter


# @pytest.mark.skipif(sys.version_info < (2, 7), reason="Python 2.7 or higher is required.")
class TestHashiVaultOptionAdapter(object):

    @pytest.mark.parametrize('option', SAMPLE_KEYS)
    def test_get_option_succeeds(self, adapter, option):
        value = adapter.get_option(option)

        assert value == SAMPLE_DICT[option]

    @pytest.mark.parametrize('option', SAMPLE_KEYS)
    def test_get_option_default_succeeds(self, adapter, option):
        value = adapter.get_option_default(option, MARKER)

        assert value == SAMPLE_DICT[option]

    @pytest.mark.parametrize('option', MISSING_KEYS)
    def test_get_option_missing_raises(self, adapter, option):
        with pytest.raises(KeyError):
            adapter.get_option(option)

    @pytest.mark.parametrize('option', SAMPLE_KEYS)
    def test_get_option_default_succeeds(self, adapter, option):
        value = adapter.get_option_default(option, MARKER)

        assert value == SAMPLE_DICT[option]

    @pytest.mark.parametrize('option', MISSING_KEYS)
    def test_get_option_default_missing_returns_default(self, adapter, option):
        value = adapter.get_option_default(option, MARKER)

        assert isinstance(value, SentinelMarker)

    @pytest.mark.parametrize('option,expected', [(o, False) for o in MISSING_KEYS]+[(o, True) for o in SAMPLE_KEYS])
    def test_has_option(self, adapter, option, expected):
        assert adapter.has_option(option) == expected

    @pytest.mark.parametrize('value', ['__VALUE'])
    @pytest.mark.parametrize('option', (SAMPLE_KEYS+MISSING_KEYS))
    def test_set_option(self, adapter, option, value, sample_dict):
        adapter.set_option(option, value)

        # first check the underlying data, then ensure the adapter refelcts the change too
        assert sample_dict[option] == value
        assert adapter.get_option(option) == value

    @pytest.mark.parametrize('default', [MARKER])
    @pytest.mark.parametrize('option,expected', [(o, SAMPLE_DICT[o]) for o in SAMPLE_KEYS]+[(o, MARKER) for o in MISSING_KEYS])
    def test_set_option_default(self, adapter, option, default, expected, sample_dict):
        value = adapter.set_option_default(option, default)

        # check return data, underlying data structure, and adapter retrieval
        assert value == expected
        assert sample_dict[option] == expected
        assert adapter.get_option(option) == expected

    @pytest.mark.parametrize('options', [SAMPLE_KEYS[0], MISSING_KEYS[0]])
    def test_set_options(self, adapter, options, sample_dict):
        update = dict([(o, '__VALUE_%i' % i) for i, o in enumerate(options)])

        adapter.set_options(**update)

        for k in SAMPLE_KEYS:
            expected = update[k] if k in update else SAMPLE_DICT[k]
            assert sample_dict[k] == expected
            assert adapter.get_option(k) == expected

        for k in MISSING_KEYS:
            if k in update:
                assert sample_dict[k] == update[k]
                assert adapter.get_option(k) == expected
            else:
                assert k not in sample_dict
                assert not adapter.has_option(k)

    @pytest.mark.parametrize('options', [[SAMPLE_KEYS[0], MISSING_KEYS[0]]])
    def test_get_options_mixed(self, adapter, options):
        with pytest.raises(KeyError):
            adapter.get_options(*options)

    @pytest.mark.parametrize('options', [MISSING_KEYS[0:2]])
    def test_get_options_missing(self, adapter, options):
        with pytest.raises(KeyError):
            adapter.get_options(*options)

    @pytest.mark.parametrize('options', [SAMPLE_KEYS[0:2]])
    def test_get_options_exists(self, adapter, options):
        expected = dict([(k, SAMPLE_DICT[k]) for k in options])

        result = adapter.get_options(*options)

        assert result == expected

    @pytest.mark.parametrize('options', [SAMPLE_KEYS[0:2]])
    def test_get_options_default_exists(self, adapter, options):
        expected = dict([(k, SAMPLE_DICT[k]) for k in options])

        result = adapter.get_options_default(MARKER, *options)

        assert result == expected

    @pytest.mark.parametrize('options', [MISSING_KEYS[0:2]])
    def test_get_options_default_missing(self, adapter, options):
        expected = dict.fromkeys(options, MARKER)

        result = adapter.get_options_default(MARKER, *options)

        assert result == expected

    @pytest.mark.parametrize('options', [[SAMPLE_KEYS[0], MISSING_KEYS[0]]])
    def test_get_options_default_mixed(self, adapter, options):
        result = adapter.get_options_default(MARKER, *options)

        for o in options:
            assert result[o] == SAMPLE_DICT.get(o, MARKER)
            assert result[o] == adapter.get_option_default(o, MARKER)

    @pytest.mark.parametrize('options', [SAMPLE_KEYS[0:2]])
    def test_get_options_default_exists_no_default(self, adapter, options):
        expected = dict([(k, SAMPLE_DICT[k]) for k in options])

        result = adapter.get_options_default(*options)

        assert result == expected

    @pytest.mark.parametrize('options', [MISSING_KEYS[0:2]])
    def test_get_options_default_missing_no_default(self, adapter, options):
        expected = dict.fromkeys(options, None)

        result = adapter.get_options_default(*options)

        assert result == expected

    @pytest.mark.parametrize('options', [[SAMPLE_KEYS[0], MISSING_KEYS[0]]])
    def test_get_options_default_mixed_no_default(self, adapter, options):
        result = adapter.get_options_default(*options)

        for o in options:
            assert result[o] == SAMPLE_DICT.get(o, None)
            assert result[o] == adapter.get_option_default(o, None)
