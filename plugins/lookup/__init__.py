# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.errors import AnsibleError
from ansible.plugins import AnsiblePlugin
from ansible.plugins.lookup import LookupBase
from ansible import constants as C
from ansible.utils.display import Display

from ansible_collections.community.hashi_vault.plugins.plugin_utils.hashi_vault_plugin import HashiVaultPlugin

display = Display()


class HashiVaultLookupBase(HashiVaultPlugin, LookupBase):

    def parse_kev_term(self, term, first_unqualified=None, plugin_name=None):
        '''parses a term string into a dictionary'''
        param_dict = {}

        if plugin_name is not None:
            plugin = plugin_name
        else:
            plugin = 'this'

        for i, param in enumerate(term.split()):
            try:
                key, value = param.split('=', 1)
            except ValueError:
                if i == 0 and first_unqualified is not None:
                    # allow first item to be specified as value only and assign to assumed option name
                    key = first_unqualified
                    value = param
                else:
                    raise AnsibleError("%s lookup plugin needs key=value pairs, but received %s" % (plugin, term))

            param_dict[key] = value

        return param_dict
