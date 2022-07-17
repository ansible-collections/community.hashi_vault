# Copyright (c) 2022 Brian Scholer (@briantist)
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

import pytest

from ansible.module_utils.six import string_types
from ansible.module_utils.common.text.converters import to_bytes
from ansible.module_utils.common._collections_compat import MutableMapping, Sequence

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
    def _process(param):
        if isinstance(param, string_types):
            args = param
            _yield = args
            return (args, _yield)
        elif isinstance(param, MutableMapping):
            if '_yield' in param:
                y = param.pop('_yield')
                _yield = dict((k, v) for k, v in param.items() if k in y)
            else:
                _yield = param

            if 'ANSIBLE_MODULE_ARGS' not in param:
                param = {'ANSIBLE_MODULE_ARGS': param}
            if '_ansible_remote_tmp' not in param['ANSIBLE_MODULE_ARGS']:
                param['ANSIBLE_MODULE_ARGS']['_ansible_remote_tmp'] = '/tmp'
            if '_ansible_keep_remote_files' not in param['ANSIBLE_MODULE_ARGS']:
                param['ANSIBLE_MODULE_ARGS']['_ansible_keep_remote_files'] = False
            args = json.dumps(param)
            return (args, _yield)
        elif isinstance(param, Sequence):
            # First item should be a dict that serves as the base of options,
            # use it for things that aren't being parametrized.
            # Each of the remaining items is the name of a fixture whose name
            # begins with opt_ (but without the opt_ prefix), and we will look those up.
            if not isinstance(param[0], MutableMapping):
                raise Exception('First value in patch_ansible_module array param must be a dict')

            margs = param[0]
            for fixt in param[1:]:
                margs[fixt] = request.getfixturevalue('opt_' + fixt)

            return _process(margs)
        else:
            raise Exception('Malformed data to the patch_ansible_module pytest fixture')

    if 'no_ansible_module_patch' in request.keywords:
        yield
    else:
        args, _yield = _process(request.param)
        with mock.patch('ansible.module_utils.basic._ANSIBLE_ARGS', to_bytes(args)):
            # TODO: in 2.10+ we can patch basic.warn instead of basic.AnsibleModule.warn
            with mock.patch('ansible.module_utils.basic.AnsibleModule.warn', module_warn):
                yield _yield
