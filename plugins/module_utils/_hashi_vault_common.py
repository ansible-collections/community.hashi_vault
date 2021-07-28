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

from ansible.module_utils.common.validation import (
    check_type_dict,
    check_type_str,
    check_type_bool,
    check_type_int,
)

HAS_HVAC = False
try:
    import hvac
    HAS_HVAC = True
except ImportError:
    HAS_HVAC = False

# we implement retries via the urllib3 Retry class
# https://github.com/ansible-collections/community.hashi_vault/issues/58
HAS_RETRIES = False
try:
    from requests import Session
    from requests.adapters import HTTPAdapter
    try:
        # try for a standalone urllib3
        from urllib3.util import Retry
        HAS_RETRIES = True
    except ImportError:
        try:
            # failing that try for a vendored version within requests
            from requests.packages.urllib3.util import Retry
            HAS_RETRIES = True
        except ImportError:
            pass
except ImportError:
    pass


class HashiVaultValueError(ValueError):
    '''Use in common code to raise an Exception that can be turned into AnsibleError or used to fail_json()'''


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
        'ca_cert': ['VAULT_CACERT'],
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

    OPTIONS = ['url', 'proxies', 'ca_cert', 'validate_certs', 'namespace', 'timeout', 'retries', 'retry_action']

    _RETRIES_DEFAULT_PARAMS = {
        'status_forcelist': [
            # https://www.vaultproject.io/api#http-status-codes
            # 429 is usually a "too many requests" status, but in Vault it's the default health status response for standby nodes.
            500,  # Internal server error. An internal error has occurred, try again later. If the error persists, report a bug.
            502,  # A request to Vault required Vault making a request to a third party; the third party responded with an error of some kind.
            503,  # Vault is down for maintenance or is currently sealed. Try again later.
        ],
        (
            # this field name changed in 1.26.0, and in the interest of supporting a wider range of urllib3 versions
            # we'll use the new name whenever possible, but fall back seamlessly when needed.
            # See also:
            # - https://github.com/urllib3/urllib3/issues/2092
            # - https://github.com/urllib3/urllib3/blob/main/CHANGES.rst#1260-2020-11-10
            "allowed_methods" if HAS_RETRIES and hasattr(Retry.DEFAULT, "allowed_methods") else "method_whitelist"
        ): None,  # None allows retries on all methods, including those which may not be considered idempotent, like POST
        'backoff_factor': 0.3,
    }

    def __init__(self, option_adapter, retry_callback_generator=None):
        super(HashiVaultConnectionOptions, self).__init__(option_adapter)
        self._retry_callback_generator = retry_callback_generator

    def get_hvac_connection_options(self):
        '''returns kwargs to be used for constructing an hvac.Client'''

        # validate_certs is only used to optionally change the value of ca_cert
        def _filter(k, v):
            return v is not None and k != 'validate_certs'

        # our transformed ca_cert value will become the verify parameter for the hvac client
        hvopts = self._options.get_filtered_options(_filter, *self.OPTIONS)
        hvopts['verify'] = hvopts.pop('ca_cert')

        retry_action = hvopts.pop('retry_action')
        if 'retries' in hvopts:
            hvopts['retries']['new_callback'] = self._retry_callback_generator(retry_action)
            hvopts['session'] = self._get_custom_requests_session(hvopts.pop('retries'))

        return hvopts

    def process_connection_options(self):
        '''executes special processing required for certain options'''
        self._boolean_or_cacert()
        self._process_option_proxies()
        self._process_option_retries()

    def _get_custom_requests_session(self, retry_kwargs):
        '''returns a requests.Session to pass to hvac (or None)'''

        if not HAS_RETRIES:
            # because hvac requires requests which requires urllib3 it's unlikely we'll ever reach this condition.
            raise NotImplementedError("Retries are unavailable. This may indicate very old versions of one or more of the following: hvac, requests, urllib3.")

        # This is defined here because Retry may not be defined if its import failed.
        # As mentioned above, that's very unlikely, but it'll fail sanity tests nonetheless if defined with other classes.
        class CallbackRetry(Retry):
            def __init__(self, *args, **kwargs):
                self._newcb = kwargs.pop('new_callback')
                super(CallbackRetry, self).__init__(*args, **kwargs)

            def new(self, **kwargs):
                if self._newcb is not None:
                    self._newcb(self)

                kwargs['new_callback'] = self._newcb
                return super(CallbackRetry, self).new(**kwargs)

        # We don't want the Retry class raising its own exceptions because that will prevent
        # hvac from raising its own on various response codes.
        # We set this here, rather than in the defaults, because if the caller sets their own
        # dict for retries, we use it directly, but we don't want them to have to remember to always
        # set raise_on_status=False themselves to get proper error handling.
        # On the off chance someone does set it, we leave it alone, even though it's probably a mistake.
        # That will be mentioned in the parameter docs.
        if 'raise_on_status' not in retry_kwargs:
            retry_kwargs['raise_on_status'] = False
            # needs urllib 1.15+ https://github.com/urllib3/urllib3/blob/main/CHANGES.rst#115-2016-04-06
            # but we should always have newer ones via requests, via hvac

        retry = CallbackRetry(**retry_kwargs)

        adapter = HTTPAdapter(max_retries=retry)
        sess = Session()
        sess.mount("https://", adapter)
        sess.mount("http://", adapter)

        return sess

    def _process_option_retries(self):
        '''check if retries option is int or dict and interpret it appropriately'''
        # this method focuses on validating the option, and setting a valid Retry object construction dict
        # it intentionally does not build the Session object, which will be done elsewhere

        retries_opt = self._options.get_option('retries')

        if retries_opt is None:
            return

        # we'll start with a copy of our defaults
        retries = self._RETRIES_DEFAULT_PARAMS.copy()

        try:
            # try int
            # on int, retry the specified number of times, and use the defaults for everything else
            # on zero, disable retries
            retries_int = check_type_int(retries_opt)

            if retries_int < 0:
                raise ValueError("Number of retries must be >= 0 (got %i)" % retries_int)
            elif retries_int == 0:
                retries = None
            else:
                retries['total'] = retries_int

        except TypeError:
            try:
                # try dict
                # on dict, use the value directly (will be used as the kwargs to initialize the Retry instance)
                retries = check_type_dict(retries_opt)
            except TypeError:
                raise TypeError("retries option must be interpretable as int or dict. Got: %r" % retries_opt)

        self._options.set_option('retries', retries)

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


class HashiVaultAuthMethodBase(HashiVaultOptionGroupBase):
    '''Base class for individual auth method implementations'''

    def __init__(self, option_adapter, warning_callback):
        super(HashiVaultAuthMethodBase, self).__init__(option_adapter)
        self._warner = warning_callback

    def validate(self):
        '''Validates the given auth method as much as possible without calling Vault.'''
        raise NotImplementedError('validate must be implemented')

    def authenticate(self, client, use_token=True):
        '''Authenticates against Vault, returns a token.'''
        raise NotImplementedError('authenticate must be implemented')

    def validate_by_required_fields(self, *field_names):
        missing = [field for field in field_names if self._options.get_option_default(field) is None]

        if missing:
            raise HashiVaultValueError("Authentication method %s requires options %r to be set, but these are missing: %r" % (self.NAME, field_names, missing))

    def warn(self, message):
        self._warner(message)


class HashiVaultAuthMethodNone(HashiVaultAuthMethodBase):
    '''HashiVault option group class for auth: none'''

    NAME = 'none'
    OPTIONS = []

    def __init__(self, option_adapter, warning_callback):
        super(HashiVaultAuthMethodNone, self).__init__(option_adapter, warning_callback)

    def validate(self):
        pass

    def authenticate(self, client, use_token=False):
        return None


class HashiVaultAuthMethodUserpass(HashiVaultAuthMethodBase):
    '''HashiVault option group class for auth: userpass'''

    NAME = 'userpass'
    OPTIONS = ['username', 'password', 'mount_point']

    def __init__(self, option_adapter, warning_callback):
        super(HashiVaultAuthMethodUserpass, self).__init__(option_adapter, warning_callback)

    def validate(self):
        self.validate_by_required_fields('username', 'password')

    def authenticate(self, client, use_token=True):
        params = self._options.get_filled_options(*self.OPTIONS)
        try:
            response = client.auth.userpass.login(**params)
        except (NotImplementedError, AttributeError):
            self.warn("HVAC should be updated to version 0.9.6 or higher. Deprecated method 'auth_userpass' will be used.")
            response = client.auth_userpass(**params)

        token = response['auth']['client_token']

        # must manually set the client token with userpass login
        # see https://github.com/hvac/hvac/issues/644
        # fixed in 0.11.0 (https://github.com/hvac/hvac/pull/733)
        # but we keep the old behavior to maintain compatibility with older hvac
        if use_token:
            client.token = token

        return token


class HashiVaultAuthMethodToken(HashiVaultAuthMethodBase):
    '''HashiVault option group class for auth: userpass'''

    NAME = 'token'
    OPTIONS = ['token', 'token_path', 'token_file', 'token_validate']

    def __init__(self, option_adapter, warning_callback):
        super(HashiVaultAuthMethodToken, self).__init__(option_adapter, warning_callback)

    def validate(self):
        if not self._options.get_option('token') and self._options.get_option('token_path'):
            token_filename = os.path.join(
                self._options.get_option('token_path'),
                self._options.get_option('token_file')
            )
            if os.path.exists(token_filename):
                with open(token_filename) as token_file:
                    self._options.set_option('token', token_file.read().strip())

        if not self._options.get_option('token'):
            raise HashiVaultValueError("No Vault Token specified or discovered.")

    def authenticate(self, client, use_token=True):
        token = self._options.get_option('token')
        if use_token:
            client.token = token

            if self._options.get_option('token_validate') and not client.is_authenticated():
                raise HashiVaultValueError("Invalid Vault Token Specified.")

        return token


class HashiVaultAuthMethodAwsIamLogin(HashiVaultAuthMethodBase):
    '''HashiVault option group class for auth: userpass'''

    NAME = 'aws_iam_login'
    OPTIONS = [
        'aws_profile',
        'aws_access_key',
        'aws_secret_key',
        'aws_security_token',
        'region',
        'aws_iam_server_id',
    ]

    def __init__(self, option_adapter, warning_callback):
        super(HashiVaultAuthMethodAwsIamLogin, self).__init__(option_adapter, warning_callback)

    def validate(self):
        params = {
            'access_key': self._options.get_option_default('aws_access_key'),
            'secret_key': self._options.get_option_default('aws_secret_key'),
        }

        mount_point = self._options.get_option_default('mount_point')
        if mount_point:
            params['mount_point'] = mount_point

        role = self._options.get_option_default('role_id')
        if role:
            params['role'] = role

        region = self._options.get_option_default('region')
        if region:
            params['region'] = region

        header_value = self._options.get_option_default('aws_iam_server_id')
        if header_value:
            params['header_value'] = header_value

        if not (params['access_key'] and params['secret_key']):
            profile = self._options.get_option_default('aws_profile')
            if profile:
                # try to load boto profile
                try:
                    import boto3
                except ImportError:
                    raise HashiVaultValueError("boto3 is required for loading a boto profile.")
                else:
                    session_credentials = boto3.session.Session(profile_name=profile).get_credentials()
            else:
                # try to load from IAM credentials
                try:
                    import botocore
                except ImportError:
                    raise HashiVaultValueError("botocore is required for loading IAM role credentials.")
                else:
                    session_credentials = botocore.session.get_session().get_credentials()

            if not session_credentials:
                raise HashiVaultValueError("No AWS credentials supplied or available.")

            params['access_key'] = session_credentials.access_key
            params['secret_key'] = session_credentials.secret_key
            if session_credentials.token:
                params['session_token'] = session_credentials.token

        self._auth_aws_iam_login_params = params

    def authenticate(self, client, use_token=True):
        params = self._auth_aws_iam_login_params
        try:
            response = client.auth.aws.iam_login(use_token=use_token, **params)
        except (NotImplementedError, AttributeError):
            self.warn("HVAC should be updated to version 0.9.3 or higher. Deprecated method 'auth_aws_iam' will be used.")
            client.auth_aws_iam(use_token=use_token, **params)

        return response['client_token']


class HashiVaultAuthMethodLdap(HashiVaultAuthMethodBase):
    '''HashiVault option group class for auth: ldap'''

    NAME = 'ldap'
    OPTIONS = ['username', 'password', 'mount_point']

    def __init__(self, option_adapter, warning_callback):
        super(HashiVaultAuthMethodLdap, self).__init__(option_adapter, warning_callback)

    def validate(self):
        self.validate_by_required_fields('username', 'password')

    def authenticate(self, client, use_token=True):
        params = self._options.get_filled_options(*self.OPTIONS)
        try:
            response = client.auth.ldap.login(use_token=use_token, **params)
        except (NotImplementedError, AttributeError):
            self.warn("HVAC should be updated to version 0.7.0 or higher. Deprecated method 'auth_ldap' will be used.")
            response = client.auth_ldap(use_token=use_token, **params)

        return response['auth']['client_token']


class HashiVaultAuthMethodApprole(HashiVaultAuthMethodBase):
    '''HashiVault option group class for auth: approle'''

    NAME = 'approle'
    OPTIONS = ['role_id', 'secret_id', 'mount_point']

    def __init__(self, option_adapter, warning_callback):
        super(HashiVaultAuthMethodApprole, self).__init__(option_adapter, warning_callback)

    def validate(self):
        self.validate_by_required_fields('role_id')

    def authenticate(self, client, use_token=True):
        params = self._options.get_filled_options(*self.OPTIONS)
        try:
            response = client.auth.approle.login(use_token=use_token, **params)
        except (NotImplementedError, AttributeError):
            self.warn("HVAC should be updated to version 0.10.6 or higher. Deprecated method 'auth_approle' will be used.")
            response = client.auth_approle(use_token=use_token, **params)

        return response['auth']['client_token']


class HashiVaultAuthMethodJwt(HashiVaultAuthMethodBase):
    '''HashiVault option group class for auth: jwt'''

    NAME = 'jwt'
    OPTIONS = ['jwt', 'role_id', 'mount_point']

    def __init__(self, option_adapter, warning_callback):
        super(HashiVaultAuthMethodJwt, self).__init__(option_adapter, warning_callback)

    def validate(self):
        self.validate_by_required_fields('role_id', 'jwt')

    def authenticate(self, client, use_token=True):
        params = self._options.get_filled_options(*self.OPTIONS)
        params['role'] = params.pop('role_id')

        if 'mount_point' in params:
            params['path'] = params.pop('mount_point')

        try:
            response = client.auth.jwt.jwt_login(**params)
        except (NotImplementedError, AttributeError):
            raise NotImplementedError("JWT authentication requires HVAC version 0.10.5 or higher.")

        token = response['auth']['client_token']

        # must manually set the client token with JWT login
        # see https://github.com/hvac/hvac/issues/644
        if use_token:
            client.token = token

        return token


class HashiVaultAuthenticator():
    def __init__(self, option_adapter, warning_callback):
        self._options = option_adapter
        self._selector = {
            'none': HashiVaultAuthMethodNone(option_adapter, warning_callback),
            'userpass': HashiVaultAuthMethodUserpass(option_adapter, warning_callback),
            'token': HashiVaultAuthMethodToken(option_adapter, warning_callback),
            'aws_iam_login': HashiVaultAuthMethodAwsIamLogin(option_adapter, warning_callback),
            'ldap': HashiVaultAuthMethodLdap(option_adapter, warning_callback),
            'approle': HashiVaultAuthMethodApprole(option_adapter, warning_callback),
            'jwt': HashiVaultAuthMethodJwt(option_adapter, warning_callback),
        }

    def _get_method_object(self, method=None):
        if method is None:
            method = self._options.get_option('auth_method')

        try:
            o_method = self._selector[method]
        except KeyError:
            raise NotImplementedError("auth method '%s' is not implemented in HashiVaultAuthenticator" % method)

        return o_method

    def validate(self, *args, **kwargs):
        method = self._get_method_object(kwargs.pop('method', None))
        method.validate(*args, **kwargs)

    def authenticate(self, *args, **kwargs):
        method = self._get_method_object(kwargs.pop('method', None))
        return method.authenticate(*args, **kwargs)
