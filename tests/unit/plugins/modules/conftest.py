# Copyright (c) 2022 Brian Scholer (@briantist)
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

import pytest

from ansible.module_utils.six import string_types
from ansible.module_utils.common.text.converters import to_bytes
from ansible.module_utils.common._collections_compat import MutableMapping

from ...compat import mock

from .....plugins.module_utils._authenticator import HashiVaultAuthenticator


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "no_ansible_module_patch: causes the patch_ansible_module fixture to have no effect"
    )


@pytest.fixture
def module_warn():
    return mock.MagicMock()


@pytest.fixture
def patch_ansible_module(request, module_warn):
    if 'no_ansible_module_patch' in request.keywords:
        yield
    else:
        if isinstance(request.param, string_types):
            args = request.param
        elif isinstance(request.param, MutableMapping):
            if 'ANSIBLE_MODULE_ARGS' not in request.param:
                request.param = {'ANSIBLE_MODULE_ARGS': request.param}
            if '_ansible_remote_tmp' not in request.param['ANSIBLE_MODULE_ARGS']:
                request.param['ANSIBLE_MODULE_ARGS']['_ansible_remote_tmp'] = '/tmp'
            if '_ansible_keep_remote_files' not in request.param['ANSIBLE_MODULE_ARGS']:
                request.param['ANSIBLE_MODULE_ARGS']['_ansible_keep_remote_files'] = False
            args = json.dumps(request.param)
        else:
            raise Exception('Malformed data to the patch_ansible_module pytest fixture')

        with mock.patch('ansible.module_utils.basic._ANSIBLE_ARGS', to_bytes(args)):
            # TODO: in 2.10+ we can patch basic.warn instead of basic.AnsibleModule.warn
            with mock.patch('ansible.module_utils.basic.AnsibleModule.warn', module_warn):
                yield


@pytest.fixture
def vault_client():
    return mock.MagicMock()


@pytest.fixture
def patch_authenticator():
    authenticator = HashiVaultAuthenticator
    authenticator.validate = lambda self: True
    authenticator.authenticate = lambda self, client: 'dummy'

    with mock.patch('ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_module.HashiVaultAuthenticator', new=authenticator):
        yield


@pytest.fixture
def patch_get_vault_client(vault_client):
    with mock.patch(
        'ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common.HashiVaultHelper.get_vault_client', return_value=vault_client
    ):
        yield
