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


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "no_ansible_module_patch: causes the patch_ansible_module fixture to have no effect"
    )


@pytest.fixture
def module_warn():
    return mock.MagicMock()


@pytest.fixture
def patch_ansible_module(request, module_warn):
    _yield = None
    if 'no_ansible_module_patch' in request.keywords:
        yield
    else:
        if isinstance(request.param, string_types):
            args = request.param
            _yield = args
        elif isinstance(request.param, MutableMapping):
            if '_yield' in request.param:
                y = request.param.pop('_yield')
                _yield = dict((k, v) for k, v in request.param.items() if k in y)
            else:
                _yield = request.param

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
                yield _yield
