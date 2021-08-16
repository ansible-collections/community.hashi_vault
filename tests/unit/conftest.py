# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
import pytest


@pytest.fixture(autouse=True)
def skip_python():
    if sys.version_info < (2, 7):
        pytest.skip('Skipping on Python %s. community.hashi_vault supports Python 2.7 and higher.' % sys.version)
