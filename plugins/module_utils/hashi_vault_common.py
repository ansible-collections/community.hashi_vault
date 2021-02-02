# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

HAS_HVAC = False
try:
    import hvac
    HAS_HVAC = True
except ImportError:
    HAS_HVAC = False


class HashiVaultHelper():
    pass
