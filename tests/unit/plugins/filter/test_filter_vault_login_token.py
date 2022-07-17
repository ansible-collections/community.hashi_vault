# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible.errors import AnsibleError

from ansible_collections.community.hashi_vault.plugins.filter.vault_login_token import vault_login_token


@pytest.fixture
def login_response(fixture_loader):
    return fixture_loader('userpass_login_response.json')


@pytest.fixture
def module_login_response(login_response):
    return {
        "login": login_response
    }


def test_vault_login_token_login_response(login_response):
    token = vault_login_token(login_response)

    assert token == login_response['auth']['client_token']


@pytest.mark.parametrize('optional_field', ['other', 'another'])
def test_vault_login_token_login_response_alternate_optionals(login_response, optional_field):
    token = vault_login_token(login_response, optional_field=optional_field)

    assert token == login_response['auth']['client_token']


def test_vault_login_token_module_login_response(module_login_response):
    token = vault_login_token(module_login_response)

    assert token == module_login_response['login']['auth']['client_token']


@pytest.mark.parametrize('optional_field', ['other', 'another'])
def test_vault_login_token_module_wrong_field(module_login_response, optional_field):
    with pytest.raises(AnsibleError, match=r"Could not find 'auth' or 'auth\.client_token' fields\. Input may not be a Vault login response\."):
        vault_login_token(module_login_response, optional_field=optional_field)


@pytest.mark.parametrize('input', [1, 'string', ['array'], ('tuple',), False])
def test_vault_login_token_wrong_types(input):
    with pytest.raises(AnsibleError, match=r"The 'vault_login_token' filter expects a dictionary\."):
        vault_login_token(input)
