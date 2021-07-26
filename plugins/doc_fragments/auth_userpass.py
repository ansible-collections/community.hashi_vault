# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    DOCUMENTATION = r'''
    options:
      username:
        description: Authentication user name.
        env:
          - name: ANSIBLE_HASHI_VAULT_USERNAME
            version_added: '1.2.0'
        vars:
          - name: ansible_hashi_vault_username
            version_added: '1.2.0'
      password:
        description: Authentication password.
        env:
          - name: ANSIBLE_HASHI_VAULT_PASSWORD
            version_added: '1.2.0'
        vars:
          - name: ansible_hashi_vault_password
            version_added: '1.2.0'
    '''
