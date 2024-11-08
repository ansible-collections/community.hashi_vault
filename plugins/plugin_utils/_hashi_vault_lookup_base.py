# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# FOR INTERNAL COLLECTION USE ONLY
# The interfaces in this file are meant for use within the community.hashi_vault collection
# and may not remain stable to outside uses. Changes may be made in ANY release, even a bugfix release.
# See also: https://github.com/ansible/community/issues/539#issuecomment-780839686
# Please open an issue if you have questions about this.

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display

from ..plugin_utils._hashi_vault_plugin import HashiVaultPlugin

display = Display()


class HashiVaultLookupBase(HashiVaultPlugin, LookupBase):

    def __init__(self, loader=None, templar=None, **kwargs):
        HashiVaultPlugin.__init__(self)
        LookupBase.__init__(self, loader=loader, templar=templar, **kwargs)
