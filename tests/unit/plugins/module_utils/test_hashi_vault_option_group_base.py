# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import pytest

from ansible_collections.community.hashi_vault.tests.unit.compat import mock

from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import (
    HashiVaultOptionGroupBase,
    HashiVaultOptionAdapter,
)


PREREAD_OPTIONS = {
    'opt1': 'val1',
    'opt2': None,
    'opt3': 'val3',
    'opt4': None,
    # no opt5
    'opt6': None,
}

LOW_PREF_DEF = {
    'opt1': dict(env=['_ENV_1A'], default='never'),
    'opt2': dict(env=['_ENV_2A', '_ENV_2B']),
    'opt4': dict(env=['_ENV_4A', '_ENV_4B', '_ENV_4C']),
    'opt5': dict(env=['_ENV_5A']),
    'opt6': dict(env=['_ENV_6A'], default='mosdefault'),
}


@pytest.fixture
def preread_options():
    return PREREAD_OPTIONS.copy()


@pytest.fixture
def adapter(preread_options):
    return HashiVaultOptionAdapter.from_dict(preread_options)


@pytest.fixture
def option_group_base(adapter):
    return HashiVaultOptionGroupBase(adapter)


@pytest.fixture(params=[
    # first dict is used to patch the environment vars
    # second dict is used to patch the current options to get them to the expected state
    #
    # envpatch, expatch
    ({}, {'opt6': 'mosdefault'}),
    ({'_ENV_1A': 'alt1a'}, {'opt6': 'mosdefault'}),
    ({'_ENV_3X': 'noop3x'}, {'opt6': 'mosdefault'}),
    ({'_ENV_2B': 'alt2b'}, {'opt2': 'alt2b', 'opt6': 'mosdefault'}),
    ({'_ENV_2A': 'alt2a', '_ENV_2B': 'alt2b'}, {'opt2': 'alt2a', 'opt6': 'mosdefault'}),
    ({'_ENV_4B': 'alt4b', '_ENV_6A': 'defnot', '_ENV_4C': 'alt4c'}, {'opt4': 'alt4b', 'opt6': 'defnot'}),
    ({'_ENV_1A': 'alt1a', '_ENV_4A': 'alt4a', '_ENV_1B': 'noop1b', '_ENV_4C': 'alt4c'}, {'opt4': 'alt4a', 'opt6': 'mosdefault'}),
    ({'_ENV_5A': 'noop5a', '_ENV_4C': 'alt4c', '_ENV_2A': 'alt2a'}, {'opt2': 'alt2a', 'opt4': 'alt4c', 'opt6': 'mosdefault'}),
])
def with_env(request, preread_options):
    envpatch, expatch = request.param

    expected = preread_options.copy()
    expected.update(expatch)

    with mock.patch.dict(os.environ, envpatch):
        yield expected


class TestHashiVaultOptionGroupBase(object):

    def test_process_late_binding_env_vars(self, option_group_base, with_env, preread_options):
        option_group_base.process_late_binding_env_vars(LOW_PREF_DEF)

        assert preread_options == with_env, "Expected: %r\nGot: %r" % (with_env, preread_options)
