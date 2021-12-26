# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
import os
import json
import pytest


@pytest.fixture(autouse=True)
def skip_python():
    if sys.version_info < (3, 6):
        pytest.skip('Skipping on Python %s. community.hashi_vault supports Python 3.6 and higher.' % sys.version)


@pytest.fixture
def fixture_loader():
    def _loader(name, parse='json'):
        here = os.path.dirname(os.path.realpath(__file__))
        fixture = os.path.join(here, 'fixtures', name)

        if parse == 'path':
            return fixture

        with open(fixture, 'r') as f:
            if parse == 'json':
                d = json.load(f)
            elif parse == 'lines':
                d = f.readlines()
            elif parse == 'raw':
                d = f.read()
            else:
                raise ValueError("Unknown value '%s' for parse" % parse)

        return d

    return _loader
