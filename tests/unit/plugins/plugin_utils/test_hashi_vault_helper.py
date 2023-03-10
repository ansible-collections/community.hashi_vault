# -*- coding: utf-8 -*-
# Copyright (c) 2022 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible.utils.unsafe_proxy import AnsibleUnsafeBytes, AnsibleUnsafeText

from ansible_collections.community.hashi_vault.tests.unit.compat import mock
from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import HashiVaultHelper


@pytest.fixture
def hashi_vault_helper():
    return HashiVaultHelper()


@pytest.fixture
def expected_stringify_candidates():
    return set([
        'token',
        'namespace',
    ])


class TestHashiVaultHelper(object):
    def test_expected_stringify_candidates(self, hashi_vault_helper, expected_stringify_candidates):
        # If we add more candidates to the set without updating the tests,
        # this will help us catch that. The purpose is not to simply update
        # the set in the fixture, but to also add specific tests where appropriate.
        assert hashi_vault_helper.STRINGIFY_CANDIDATES == expected_stringify_candidates, '%r' % (
            hashi_vault_helper.STRINGIFY_CANDIDATES ^ expected_stringify_candidates
        )

    @pytest.mark.parametrize('input', [b'one', u'two', AnsibleUnsafeBytes(b'three'), AnsibleUnsafeText(u'four')])
    @pytest.mark.parametrize('stringify', [True, False])
    def test_get_vault_client_stringify(self, hashi_vault_helper, expected_stringify_candidates, input, stringify):
        kwargs = {
            '__no_candidate': AnsibleUnsafeText(u'value'),
        }
        expected_calls = []
        for k in expected_stringify_candidates:
            v = '%s_%s' % (k, input)
            kwargs[k] = v
            if stringify:
                expected_calls.append(mock.call(v))

        wrapper = mock.Mock(wraps=hashi_vault_helper._stringify)
        with mock.patch('hvac.Client'):
            with mock.patch.object(hashi_vault_helper, '_stringify', wrapper):
                hashi_vault_helper.get_vault_client(hashi_vault_stringify_args=stringify, **kwargs)

        assert wrapper.call_count == len(expected_calls)
        wrapper.assert_has_calls(expected_calls)
