# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ......plugins.module_utils._hashi_vault_common import HashiVaultOptionAdapter


SAMPLE_DICT = {
    'key1': 'val1',
    'key2': 2,
    'key3': 'three',
    'key4': 'iiii',
    'key5': None,
}

SAMPLE_KEYS = sorted(list(SAMPLE_DICT.keys()))

MISSING_KEYS = ['no', 'nein', 'iie']


class SentinelMarker():
    pass


MARKER = SentinelMarker()


@pytest.fixture()
def sample_dict():
    return SAMPLE_DICT.copy()


@pytest.fixture
def adapter_from_dict(sample_dict):
    def _create_adapter_from_dict():
        return HashiVaultOptionAdapter.from_dict(sample_dict)

    return _create_adapter_from_dict


@pytest.fixture
def adapter_from_dict_defaults(sample_dict):
    # the point of this one is to test the "default" methods provided by the adapter
    # for everything except getter and setter, so we only supply those two required methods
    def _create_adapter_from_dict_defaults():
        return HashiVaultOptionAdapter(getter=sample_dict.__getitem__, setter=sample_dict.__setitem__)

    return _create_adapter_from_dict_defaults


@pytest.fixture
def filter_all():
    return lambda k, v: True


@pytest.fixture
def filter_none():
    return lambda k, v: False


@pytest.fixture
def filter_value_not_none():
    return lambda k, v: v is not None


@pytest.fixture
def filter_key_in_range():
    return lambda k, v: k in SAMPLE_KEYS[1:3]


class TestHashiVaultOptionAdapter(object):

    @pytest.mark.parametrize('option', SAMPLE_KEYS)
    def test_get_option_succeeds(self, adapter, option):
        value = adapter.get_option(option)

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

    @pytest.mark.parametrize('option,expected', [(o, False) for o in MISSING_KEYS] + [(o, True) for o in SAMPLE_KEYS])
    def test_has_option(self, adapter, option, expected):
        assert adapter.has_option(option) == expected

    @pytest.mark.parametrize('option', SAMPLE_KEYS)
    def test_set_option_existing(self, adapter, option, sample_dict):
        value = type(sample_dict.get(option, ""))()
        adapter.set_option(option, value)
        # first check the underlying data, then ensure the adapter refelcts the change too
        assert sample_dict[option] == value
        assert adapter.get_option(option) == value

    @pytest.mark.parametrize('option', MISSING_KEYS)
    def test_set_option_missing(self, request, adapter, option, sample_dict):
        value = MARKER

        for mark in request.node.own_markers:
            if mark.name == 'option_adapter_raise_on_missing':
                try:
                    # https://github.com/ansible/ansible/commit/35750ed3218e7bce68b21f473cecb0a3b9d60321#diff-25bf290f4a4aeb2a7adceda321671603c1023a7585b8634afea0e37d3064628eL671
                    # 2.19 added a dedicated error for this
                    from ansible.errors import AnsibleUndefinedConfigEntry
                except ImportError:
                    # pre-2.19
                    from ansible.errors import AnsibleError
                    with pytest.raises(AnsibleError, match=rf"^Requested entry.*?setting: {option}.*?was not defined in configuration"):
                        adapter.set_option(option, value)
                else:
                    with pytest.raises(AnsibleUndefinedConfigEntry):
                        adapter.set_option(option, value)
                break
        else:
            adapter.set_option(option, value)
            assert sample_dict[option] == value
            assert adapter.get_option(option) == value

    @pytest.mark.parametrize('default', [MARKER])
    @pytest.mark.parametrize('option,expected', [(o, SAMPLE_DICT[o]) for o in SAMPLE_KEYS])
    def test_set_option_default_existing(self, adapter, option, default, expected, sample_dict):
        value = adapter.set_option_default(option, default)

        # check return data, underlying data structure, and adapter retrieval
        assert value == expected
        assert sample_dict[option] == expected
        assert adapter.get_option(option) == expected

    @pytest.mark.parametrize('default', [MARKER])
    @pytest.mark.parametrize('option,expected', [(o, MARKER) for o in MISSING_KEYS])
    def test_set_option_default_missing(self, request, adapter, option, default, expected, sample_dict):
        for mark in request.node.own_markers:
            if mark.name == 'option_adapter_raise_on_missing':
                try:
                    # https://github.com/ansible/ansible/commit/35750ed3218e7bce68b21f473cecb0a3b9d60321#diff-25bf290f4a4aeb2a7adceda321671603c1023a7585b8634afea0e37d3064628eL671
                    # 2.19 added a dedicated error for this
                    from ansible.errors import AnsibleUndefinedConfigEntry
                except ImportError:
                    # pre-2.19
                    from ansible.errors import AnsibleError
                    with pytest.raises(AnsibleError, match=rf"^Requested entry.*?setting: {option}.*?was not defined in configuration"):
                        adapter.set_option(option, default)
                else:
                    with pytest.raises(AnsibleUndefinedConfigEntry):
                        adapter.set_option(option, default)
                break
        else:
            value = adapter.set_option_default(option, default)
            # check return data, underlying data structure, and adapter retrieval
            assert value == expected
            assert sample_dict[option] == expected
            assert adapter.get_option(option) == expected

    @pytest.mark.parametrize('options', [[SAMPLE_KEYS[0], MISSING_KEYS[0]]])
    def test_set_options(self, request, adapter, options, sample_dict):
        update = dict([(o, type(sample_dict.get(o, ""))(i)) for i, o in enumerate(options)])

        for mark in request.node.own_markers:
            if mark.name == 'option_adapter_raise_on_missing':
                try:
                    # https://github.com/ansible/ansible/commit/35750ed3218e7bce68b21f473cecb0a3b9d60321#diff-25bf290f4a4aeb2a7adceda321671603c1023a7585b8634afea0e37d3064628eL671
                    # 2.19 added a dedicated error for this
                    from ansible.errors import AnsibleUndefinedConfigEntry
                except ImportError:
                    # pre-2.19
                    from ansible.errors import AnsibleError
                    with pytest.raises(AnsibleError, match=r"^Requested entry.*?setting:.*?was not defined in configuration"):
                        adapter.set_options(**update)
                else:
                    with pytest.raises(AnsibleUndefinedConfigEntry):
                        adapter.set_options(**update)
                break
        else:
            adapter.set_options(**update)
            for k in MISSING_KEYS:
                if k in update:
                    assert sample_dict[k] == update[k]
                    assert adapter.get_option(k) == update[k]
                else:
                    assert k not in sample_dict
                    assert not adapter.has_option(k)

        for k in SAMPLE_KEYS:
            expected = update[k] if k in update else SAMPLE_DICT[k]
            assert sample_dict[k] == expected
            assert adapter.get_option(k) == expected

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

    @pytest.mark.parametrize('options', [[SAMPLE_KEYS[0], MISSING_KEYS[0]]])
    def test_get_filtered_options_mixed(self, adapter, options, filter_all):
        with pytest.raises(KeyError):
            adapter.get_filtered_options(filter_all, *options)

    @pytest.mark.parametrize('options', [MISSING_KEYS[0:2]])
    def test_get_filtered_options_missing(self, adapter, options, filter_all):
        with pytest.raises(KeyError):
            adapter.get_filtered_options(filter_all, *options)

    @pytest.mark.parametrize('options', [SAMPLE_KEYS])
    def test_get_filtered_options_all(self, adapter, options, filter_all):
        expected = dict([(k, SAMPLE_DICT[k]) for k in options])

        result = adapter.get_filtered_options(filter_all, *options)

        assert result == expected
        assert result == adapter.get_options(*options)

    @pytest.mark.parametrize('options', [SAMPLE_KEYS])
    def test_get_filtered_options_none(self, adapter, options, filter_none):
        expected = {}

        result = adapter.get_filtered_options(filter_none, *options)

        assert result == expected

    @pytest.mark.parametrize('options', [SAMPLE_KEYS])
    def test_get_filtered_options_by_value(self, adapter, options, filter_value_not_none):
        expected = dict([(k, SAMPLE_DICT[k]) for k in options if SAMPLE_DICT[k] is not None])

        result = adapter.get_filtered_options(filter_value_not_none, *options)

        assert result == expected

    @pytest.mark.parametrize('options', [SAMPLE_KEYS])
    def test_get_filtered_options_by_key(self, adapter, options, filter_key_in_range):
        expected = dict([(k, SAMPLE_DICT[k]) for k in options if k in SAMPLE_KEYS[1:3]])

        result = adapter.get_filtered_options(filter_key_in_range, *options)

        assert result == expected

    @pytest.mark.parametrize('options', [SAMPLE_KEYS])
    def test_get_filled_options(self, adapter, options):
        expected = dict([(k, SAMPLE_DICT[k]) for k in options if SAMPLE_DICT[k] is not None])

        result = adapter.get_filled_options(*options)

        assert result == expected
