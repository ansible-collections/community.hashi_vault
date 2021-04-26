# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

# this file is here just to run the exact same tests as written in the imported file, with the main difference
# being the fixtures defined in conftest.py (this version can run tests that rely on controller-side code)
# and the supported python versions being different.
# So we really do want to import * and so we disable lint failure on wildcard imports.
#
# pylint: disable=wildcard-import,unused-wildcard-import
from ansible_collections.community.hashi_vault.tests.unit.plugins.module_utils.option_adapter.test_hashi_vault_option_adapter import *
