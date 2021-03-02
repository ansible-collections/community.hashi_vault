# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

'''Python versions supported: all controller-side versions, all remote-side versions except 2.6'''

# FOR INTERNAL COLLECTION USE ONLY
# The interfaces in this file are meant for use within the community.hashi_vault collection
# and may not remain stable to outside uses. Changes may be made in ANY release, even a bugfix release.
# See also: https://github.com/ansible/community/issues/539#issuecomment-780839686
# Please open an issue if you have questions about this.

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os

from ansible.module_utils.common.validation import check_type_dict, check_type_str, check_type_bool

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


class HashiVaultOptionAdapter(object):
    '''
    The purpose of this class is to provide a standard interface for option getting/setting
    within module_utils code, since the processes are so different in plugins and modules.

    Attention is paid to ensuring that in plugins we use the methods provided by Config Manager,
    but to allow flexibility to create an adapter to work with other sources, hence the design
    of defining specific methods exposed, and having them call provided function references.
    '''
    # More context on the need to call Config Manager methods:
    #
    # Some issues raised around deprecations in plugins not being processed led to comments
    # from core maintainers around the need to use Config Manager and also to ensure any
    # option needed is always retrieved using AnsiblePlugin.get_option(). At the time of this
    # writing, based on the way Config Manager is implemented, that's not actually necessary,
    # and calling AnsiblePlugin.set_options() to initialize them is enough. But that's not
    # guaranteed to stay that way, if get_option() is used to "trigger" internal events.
    #
    # More reading:
    # - https://github.com/ansible-collections/community.hashi_vault/issues/35
    # - https://github.com/ansible/ansible/issues/73051
    # - https://github.com/ansible/ansible/pull/73058
    # - https://github.com/ansible/ansible/pull/73239
    # - https://github.com/ansible/ansible/pull/73240

    @classmethod
    def from_dict(cls, dict):
        return cls(
            getter=dict.__getitem__,
            setter=dict.__setitem__,
            haver=lambda key: key in dict,
            updater=dict.update,
            defaultsetter=dict.setdefault,
            defaultgetter=dict.get,
        )

    @classmethod
    def from_ansible_plugin(cls, plugin):
        return cls(
            getter=plugin.get_option,
            setter=plugin.set_option,
            haver=plugin.has_option if hasattr(plugin, 'has_option') else None,
            # AnsiblePlugin.has_option was added in 2.10, see https://github.com/ansible/ansible/pull/61078
        )

    def __init__(
            self,
            getter, setter,
            haver=None, updater=None, getitems=None, getfiltereditems=None, getfilleditems=None, defaultsetter=None, defaultgetter=None):

        def _default_default_setter(key, default=None):
            try:
                value = self.get_option(key)
                return value
            except KeyError:
                self.set_option(key, default)
                return default

        def _default_updater(**kwargs):
            for key, value in kwargs.items():
                self.set_option(key, value)

        def _default_haver(key):
            try:
                self.get_option(key)
                return True
            except KeyError:
                return False

        def _default_getitems(*args):
            return dict((key, self.get_option(key)) for key in args)

        def _default_getfiltereditems(filter, *args):
            return dict((key, value) for key, value in self.get_options(*args).items() if filter(key, value))

        def _default_getfilleditems(*args):
            return self.get_filtered_options(lambda k, v: v is not None, *args)

        def _default_default_getter(key, default):
            try:
                return self.get_option(key)
            except KeyError:
                return default

        self._getter = getter
        self._setter = setter

        self._haver = haver or _default_haver
        self._updater = updater or _default_updater
        self._getitems = getitems or _default_getitems
        self._getfiltereditems = getfiltereditems or _default_getfiltereditems
        self._getfilleditems = getfilleditems or _default_getfilleditems
        self._defaultsetter = defaultsetter or _default_default_setter
        self._defaultgetter = defaultgetter or _default_default_getter

    def get_option(self, key):
        return self._getter(key)

    def get_option_default(self, key, default=None):
        return self._defaultgetter(key, default)

    def set_option(self, key, value):
        return self._setter(key, value)

    def set_option_default(self, key, default=None):
        return self._defaultsetter(key, default)

    def has_option(self, key):
        return self._haver(key)

    def set_options(self, **kwargs):
        return self._updater(**kwargs)

    def get_options(self, *args):
        return self._getitems(*args)

    def get_filtered_options(self, filter, *args):
        return self._getfiltereditems(filter, *args)

    def get_filled_options(self, *args):
        return self._getfilleditems(*args)


class HashiVaultOptionGroupBase:
    '''A base class for class option group classes'''

    # see https://github.com/ansible-collections/community.hashi_vault/issues/10
    #
    # Options which seek to use environment vars that are not Ansible-specific
    # should load those as values of last resort, so that INI values can override them.
    # For default processing, list such options and vars here.
    # Alternatively, process them in another appropriate place like an auth method's
    # validate_ method.
    #
    # key = option_name
    # value = list of env vars (in order of those checked first; process stops when value is found)

    # for now copying here
    # going to re-think where to specify these
    _LOW_PRECEDENCE_ENV_VAR_OPTIONS = {
        'token_path': ['HOME'],
        'namespace': ['VAULT_NAMESPACE'],
        'token': ['VAULT_TOKEN'],
        'url': ['VAULT_ADDR'],
    }

    def __init__(self, option_adapter):
        self._options = option_adapter

    def process_low_preference_env_vars(self, option_vars=None):
        ov = option_vars or self._LOW_PRECEDENCE_ENV_VAR_OPTIONS
        for opt, envs in ov.items():
            for env in envs:
                if self._options.has_option(opt) and self._options.get_option(opt) is None:
                    self._options.set_option(opt, os.environ.get(env))


class HashiVaultConnectionOptions(HashiVaultOptionGroupBase):
    '''HashiVault option group class for connection options'''

    OPTIONS = ['url', 'proxies', 'ca_cert', 'validate_certs', 'namespace']

    def __init__(self, option_adapter):
        super(HashiVaultConnectionOptions, self).__init__(option_adapter)

    def get_hvac_connection_options(self):
        # validate_certs is only used to optonally change the value of ca_cert
        def _filter(k, v):
            return v is not None and k != 'validate_certs'

        # our transformed ca_cert value will become the verify parameter for the hvac client
        hvopts = self._options.get_filtered_options(_filter, *self.OPTIONS)
        hvopts['verify'] = hvopts.pop('ca_cert')

        return hvopts

    def process_connection_options(self):
        '''executes special processing required for certain options'''
        self._boolean_or_cacert()
        self._process_option_proxies()

    def _process_option_proxies(self):
        '''check if 'proxies' option is dict or str and set it appropriately'''

        proxies_opt = self._options.get_option('proxies')

        if proxies_opt is None:
            return

        try:
            # if it can be interpreted as dict
            # do it
            proxies = check_type_dict(proxies_opt)
        except TypeError:
            # if it can't be interpreted as dict
            proxy = check_type_str(proxies_opt)
            # but can be interpreted as str
            # use this str as http and https proxy
            proxies = {
                'http': proxy,
                'https': proxy,
            }

        # record the new/interpreted value for 'proxies' option
        self._options.set_option('proxies', proxies)

    def _boolean_or_cacert(self):
        # This is needed because of this (https://hvac.readthedocs.io/en/stable/source/hvac_v1.html):
        #
        # # verify (Union[bool,str]) - Either a boolean to indicate whether TLS verification should
        # # be performed when sending requests to Vault, or a string pointing at the CA bundle to use for verification.
        #
        '''return a bool or cacert'''
        ca_cert = self._options.get_option('ca_cert')

        validate_certs = self._options.get_option('validate_certs')

        if validate_certs is None:
            # Validate certs option was not explicitly set

            # Check if VAULT_SKIP_VERIFY is set
            vault_skip_verify = os.environ.get('VAULT_SKIP_VERIFY')

            if vault_skip_verify is not None:
                # VAULT_SKIP_VERIFY is set
                try:
                    # Check that we have a boolean value
                    vault_skip_verify = check_type_bool(vault_skip_verify)
                    # Use the inverse of VAULT_SKIP_VERIFY
                    validate_certs = not vault_skip_verify
                except TypeError:
                    # Not a boolean value fallback to default value (True)
                    validate_certs = True
            else:
                validate_certs = True

        if not (validate_certs and ca_cert):
            self._options.set_option('ca_cert', validate_certs)
