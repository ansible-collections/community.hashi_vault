# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

# this file must define the "adapter" fixture at a minimum,
# and anything else that it needs or depends on that isn't already defined in in the test files themselves.

# Keep in mind that this one is for module_utils and so it cannot depend on or import any controller-side code.

import pytest


@pytest.fixture(params=['dict', 'dict_defaults'])
def adapter(request, adapter_from_dict, adapter_from_dict_defaults):
    return {
        'dict': adapter_from_dict,
        'dict_defaults': adapter_from_dict_defaults,
    }[request.param]()
