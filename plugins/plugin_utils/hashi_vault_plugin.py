# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.plugins import AnsiblePlugin
from ansible import constants as C
from ansible.utils.display import Display

from ansible_collections.community.hashi_vault.plugins.module_utils.hashi_vault_common import HashiVaultHelper

display = Display()


class HashiVaultPlugin(AnsiblePlugin):
    def __init__(self, loader=None, templar=None, **kwargs):
        super(HashiVaultPlugin, self).__init__()

        self._helper = HashiVaultHelper()

    def deprecate(self, collection_name='community.hashi_vault'):
        '''processes deprecations related to the collection'''

        # TODO: this is a workaround for deprecations not being shown in lookups
        # See: https://github.com/ansible/ansible/issues/73051
        # Fix: https://github.com/ansible/ansible/pull/73058
        #
        # If #73058 or another fix is backported, this should be removed.

        # nicked from cli/__init__.py
        # with slight customizations to help filter out relevant messages
        # (relying on the collection name since it's a valid attrib and we only have 1 plugin at this time)

        # warn about deprecated config options

        for deprecated in list(C.config.DEPRECATED):
            name = deprecated[0]
            why = deprecated[1]['why']
            if deprecated[1].get('collection_name') != collection_name:
                continue

            if 'alternatives' in deprecated[1]:
                alt = ', use %s instead' % deprecated[1]['alternatives']
            else:
                alt = ''
            ver = deprecated[1].get('version')
            date = deprecated[1].get('date')
            collection_name = deprecated[1].get('collection_name')
            display.deprecated("%s option, %s%s" % (name, why, alt), version=ver, date=date, collection_name=collection_name)

            # remove this item from the list so it won't get processed again by something else
            C.config.DEPRECATED.remove(deprecated)
