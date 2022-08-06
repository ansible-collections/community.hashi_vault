# -*- coding: utf-8 -*-
# Copyright (c) 2022 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible.utils.unsafe_proxy import AnsibleUnsafe, AnsibleUnsafeBytes, AnsibleUnsafeText

from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import _stringify


@pytest.fixture
def uvalue():
    return u'fake123'


@pytest.fixture
def bvalue():
    return b'fake456'


class TestHashiVaultCommonStringify(object):
    @pytest.mark.parametrize('unsafe', [True, False])
    def test_stringify_bytes(self, unsafe, bvalue):
        token = bvalue
        if unsafe:
            token = AnsibleUnsafeBytes(token)

        r = _stringify(token)

        assert isinstance(r, bytes)
        assert not isinstance(r, AnsibleUnsafe)

    @pytest.mark.parametrize('unsafe', [True, False])
    def test_stringify_unicode(self, unsafe, uvalue):
        token = uvalue
        utype = type(token)
        if unsafe:
            token = AnsibleUnsafeText(token)

        r = _stringify(token)

        assert isinstance(r, utype)
        assert not isinstance(r, AnsibleUnsafe)
