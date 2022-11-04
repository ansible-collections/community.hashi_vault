# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    DOCUMENTATION = r'''
options: {}
'''

    ACTION_GROUP = r'''
options: {}
attributes:
  action_group:
    description: Use C(group/community.hashi_vault.vault) in C(module_defaults) to set defaults for this module.
    support: full
    membership:
      - community.hashi_vault.vault
'''

    CHECK_MODE_READ_ONLY = r'''
options: {}
attributes:
  check_mode:
    support: full
    description: This module is "read only" and operates the same regardless of check mode.
'''
