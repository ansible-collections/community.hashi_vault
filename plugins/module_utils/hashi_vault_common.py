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

    def __init__(self):
        # TODO move hvac checking here?
        pass

    def get_vault_client(self, hashi_vault_logout_inferred_token=True, hashi_vault_revoke_on_logout=False, **kwargs):
        '''
        creates a Vault client with the given kwargs

        :param hashi_vault_logout_inferred_token: if True performs "logout" after creation to remove any token that
        the hvac library itself may have read in. Only used if "token" is not included in kwargs.
        :type hashi_vault_logout_implied_token: bool

        :param hashi_vault_revoke_on_logout: if True revokes any current token on logout. Only used if a logout is performed. Not recommended.
        :type hashi_vault_revoke_on_logout: bool
        '''

        client = hvac.Client(**kwargs)

        # logout to prevent accidental use of inferred tokens
        # https://github.com/ansible-collections/community.hashi_vault/issues/13
        if hashi_vault_logout_inferred_token and 'token' not in kwargs:
            client.logout(revoke_token=hashi_vault_revoke_on_logout)

        return client
