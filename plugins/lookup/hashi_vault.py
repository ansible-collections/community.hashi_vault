# (c) 2020, Brian Scholer (@briantist)
# (c) 2015, Jonathan Davila <jonathan(at)davila.io>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
  lookup: hashi_vault
  author:
    - Jonathan Davila (!UNKNOWN) <jdavila(at)ansible.com>
    - Brian Scholer (@briantist)
  short_description: Retrieve secrets from HashiCorp's Vault
  requirements:
    - hvac (python library)
    - hvac 0.7.0+ (for namespace support)
    - hvac 0.9.6+ (to avoid most deprecation warnings)
    - hvac 0.10.5+ (for JWT auth)
    - hvac 0.10.6+ (to avoid deprecation warning for AppRole)
    - botocore (only if inferring aws params from boto)
    - boto3 (only if using a boto profile)
  description:
    - Retrieve secrets from HashiCorp's Vault.
  notes:
    - Due to a current limitation in the HVAC library there won't necessarily be an error if a bad endpoint is specified.
    - As of community.hashi_vault 0.1.0, only the latest version of a secret is returned when specifying a KV v2 path.
    - As of community.hashi_vault 0.1.0, all options can be supplied via term string (space delimited key=value pairs) or by parameters (see examples).
    - As of community.hashi_vault 0.1.0, when I(secret) is the first option in the term string, C(secret=) is not required (see examples).
  extends_documentation_fragment: community.hashi_vault.connection
  options:
    secret:
      description: Vault path to the secret being requested in the format C(path[:field]).
      required: True
    token:
      description:
        - Vault token. Token may be specified explicitly, through the listed [env] vars, and also through the C(VAULT_TOKEN) env var.
        - If no token is supplied, explicitly or through env, then the plugin will check for a token file, as determined by I(token_path) and I(token_file).
        - The order of token loading (first found wins) is C(token param -> ansible var -> ANSIBLE_HASHI_VAULT_TOKEN -> VAULT_TOKEN -> token file).
      env:
        - name: ANSIBLE_HASHI_VAULT_TOKEN
          version_added: '0.2.0'
      vars:
        - name: ansible_hashi_vault_token
          version_added: '1.2.0'
    token_path:
      description: If no token is specified, will try to read the I(token_file) from this path.
      env:
        - name: VAULT_TOKEN_PATH
          deprecated:
            why: standardizing environment variables
            version: 2.0.0
            collection_name: community.hashi_vault
            alternatives: ANSIBLE_HASHI_VAULT_TOKEN_PATH
        - name: ANSIBLE_HASHI_VAULT_TOKEN_PATH
          version_added: '0.2.0'
      ini:
        - section: lookup_hashi_vault
          key: token_path
      vars:
        - name: ansible_hashi_vault_token_path
          version_added: '1.2.0'
    token_file:
      description: If no token is specified, will try to read the token from this file in I(token_path).
      env:
        - name: VAULT_TOKEN_FILE
          deprecated:
            why: standardizing environment variables
            version: 2.0.0
            collection_name: community.hashi_vault
            alternatives: ANSIBLE_HASHI_VAULT_TOKEN_FILE
        - name: ANSIBLE_HASHI_VAULT_TOKEN_FILE
          version_added: '0.2.0'
      ini:
        - section: lookup_hashi_vault
          key: token_file
      vars:
        - name: ansible_hashi_vault_token_file
          version_added: '1.2.0'
      default: '.vault-token'
    token_validate:
      description:
        - For token auth, will perform a C(lookup-self) operation to determine the token's validity before using it.
        - Disable if your token doesn't have the C(lookup-self) capability.
      env:
        - name: ANSIBLE_HASHI_VAULT_TOKEN_VALIDATE
      ini:
        - section: lookup_hashi_vault
          key: token_validate
      vars:
        - name: ansible_hashi_vault_token_validate
          version_added: '1.2.0'
      type: boolean
      default: true
      version_added: 0.2.0
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
    role_id:
      description: Vault Role ID. Used in approle and aws_iam_login auth methods.
      env:
        - name: VAULT_ROLE_ID
          deprecated:
            why: standardizing environment variables
            version: 2.0.0
            collection_name: community.hashi_vault
            alternatives: ANSIBLE_HASHI_VAULT_ROLE_ID
        - name: ANSIBLE_HASHI_VAULT_ROLE_ID
          version_added: '0.2.0'
      ini:
        - section: lookup_hashi_vault
          key: role_id
      vars:
        - name: ansible_hashi_vault_role_id
          version_added: '1.2.0'
    secret_id:
      description: Secret ID to be used for Vault AppRole authentication.
      env:
        - name: VAULT_SECRET_ID
          deprecated:
            why: standardizing environment variables
            version: 2.0.0
            collection_name: community.hashi_vault
            alternatives: ANSIBLE_HASHI_VAULT_SECRET_ID
        - name: ANSIBLE_HASHI_VAULT_SECRET_ID
          version_added: '0.2.0'
      vars:
        - name: ansible_hashi_vault_secret_id
          version_added: '1.2.0'
    auth_method:
      description:
        - Authentication method to be used.
        - C(none) auth method was added in collection version C(1.2.0).
      env:
        - name: VAULT_AUTH_METHOD
          deprecated:
            why: standardizing environment variables
            version: 2.0.0
            collection_name: community.hashi_vault
            alternatives: ANSIBLE_HASHI_VAULT_AUTH_METHOD
        - name: ANSIBLE_HASHI_VAULT_AUTH_METHOD
          version_added: '0.2.0'
      ini:
        - section: lookup_hashi_vault
          key: auth_method
      vars:
        - name: ansible_hashi_vault_auth_method
          version_added: '1.2.0'
      choices:
        - token
        - userpass
        - ldap
        - approle
        - aws_iam_login
        - jwt
        - none
      default: token
    return_format:
      description:
        - Controls how multiple key/value pairs in a path are treated on return.
        - C(dict) returns a single dict containing the key/value pairs.
        - C(values) returns a list of all the values only. Use when you don't care about the keys.
        - C(raw) returns the actual API result (deserialized), which includes metadata and may have the data nested in other keys.
      choices:
        - dict
        - values
        - raw
      default: dict
      aliases: [ as ]
    mount_point:
      description:
        - Vault mount point.
        - If not specified, the default mount point for a given auth method is used.
        - Does not apply to token authentication.
    jwt:
      description: The JSON Web Token (JWT) to use for JWT authentication to Vault.
      env:
        - name: ANSIBLE_HASHI_VAULT_JWT
    aws_profile:
      description: The AWS profile
      type: str
      aliases: [ boto_profile ]
      env:
        - name: AWS_DEFAULT_PROFILE
        - name: AWS_PROFILE
    aws_access_key:
      description: The AWS access key to use.
      type: str
      aliases: [ aws_access_key_id ]
      env:
        - name: EC2_ACCESS_KEY
        - name: AWS_ACCESS_KEY
        - name: AWS_ACCESS_KEY_ID
    aws_secret_key:
      description: The AWS secret key that corresponds to the access key.
      type: str
      aliases: [ aws_secret_access_key ]
      env:
        - name: EC2_SECRET_KEY
        - name: AWS_SECRET_KEY
        - name: AWS_SECRET_ACCESS_KEY
    aws_security_token:
      description: The AWS security token if using temporary access and secret keys.
      type: str
      env:
        - name: EC2_SECURITY_TOKEN
        - name: AWS_SESSION_TOKEN
        - name: AWS_SECURITY_TOKEN
    region:
      description: The AWS region for which to create the connection.
      type: str
      env:
        - name: EC2_REGION
        - name: AWS_REGION
    aws_iam_server_id:
      description: If specified, sets the value to use for the C(X-Vault-AWS-IAM-Server-ID) header as part of C(GetCallerIdentity) request.
      env:
        - name: ANSIBLE_HASHI_VAULT_AWS_IAM_SERVER_ID
      ini:
        - section: lookup_hashi_vault
          key: aws_iam_server_id
      required: False
      version_added: '0.2.0'
"""

EXAMPLES = """
- ansible.builtin.debug:
    msg: "{{ lookup('community.hashi_vault.hashi_vault', 'secret=secret/hello:value token=c975b780-d1be-8016-866b-01d0f9b688a5 url=http://myvault:8200') }}"

- name: Return all secrets from a path
  ansible.builtin.debug:
    msg: "{{ lookup('community.hashi_vault.hashi_vault', 'secret=secret/hello token=c975b780-d1be-8016-866b-01d0f9b688a5 url=http://myvault:8200') }}"

- name: Vault that requires authentication via LDAP
  ansible.builtin.debug:
    msg: "{{ lookup('community.hashi_vault.hashi_vault', 'secret/hello:value auth_method=ldap mount_point=ldap username=myuser password=mypas') }}"

- name: Vault that requires authentication via username and password
  ansible.builtin.debug:
    msg: "{{ lookup('community.hashi_vault.hashi_vault', 'secret=secret/hola:val auth_method=userpass username=myuser password=psw url=http://vault:8200') }}"

- name: Connect to Vault using TLS
  ansible.builtin.debug:
    msg: "{{ lookup('community.hashi_vault.hashi_vault', 'secret=secret/hola:value token=c975b780-d1be-8016-866b-01d0f9b688a5 validate_certs=False') }}"

- name: using certificate auth
  ansible.builtin.debug:
    msg: "{{ lookup('community.hashi_vault.hashi_vault', 'secret/hi:val token=xxxx url=https://vault:8200 validate_certs=True cacert=/cacert/path/ca.pem') }}"

- name: Authenticate with a Vault app role
  ansible.builtin.debug:
    msg: "{{ lookup('community.hashi_vault.hashi_vault', 'secret=secret/hello:value auth_method=approle role_id=myroleid secret_id=mysecretid') }}"

- name: Return all secrets from a path in a namespace
  ansible.builtin.debug:
    msg: "{{ lookup('community.hashi_vault.hashi_vault', 'secret=secret/hello token=c975b780-d1be-8016-866b-01d0f9b688a5 namespace=teama/admins') }}"

# When using KV v2 the PATH should include "data" between the secret engine mount and path (e.g. "secret/data/:path")
# see: https://www.vaultproject.io/api/secret/kv/kv-v2.html#read-secret-version
- name: Return latest KV v2 secret from path
  ansible.builtin.debug:
    msg: "{{ lookup('community.hashi_vault.hashi_vault', 'secret=secret/data/hello token=my_vault_token url=http://myvault_url:8200') }}"

# The following examples show more modern syntax, with parameters specified separately from the term string.

- name: secret= is not required if secret is first
  ansible.builtin.debug:
    msg: "{{ lookup('community.hashi_vault.hashi_vault', 'secret/data/hello token=<token> url=http://myvault_url:8200') }}"

- name: options can be specified as parameters rather than put in term string
  ansible.builtin.debug:
    msg: "{{ lookup('community.hashi_vault.hashi_vault', 'secret/data/hello', token=my_token_var, url='http://myvault_url:8200') }}"

# return_format (or its alias 'as') can control how secrets are returned to you
- name: return secrets as a dict (default)
  ansible.builtin.set_fact:
    my_secrets: "{{ lookup('community.hashi_vault.hashi_vault', 'secret/data/manysecrets', token=my_token_var, url='http://myvault_url:8200') }}"
- ansible.builtin.debug:
    msg: "{{ my_secrets['secret_key'] }}"
- ansible.builtin.debug:
    msg: "Secret '{{ item.key }}' has value '{{ item.value }}'"
  loop: "{{ my_secrets | dict2items }}"

- name: return secrets as values only
  ansible.builtin.debug:
    msg: "A secret value: {{ item }}"
  loop: "{{ query('community.hashi_vault.hashi_vault', 'secret/data/manysecrets', token=my_token_var, url='http://vault_url:8200', return_format='values') }}"

- name: return raw secret from API, including metadata
  ansible.builtin.set_fact:
    my_secret: "{{ lookup('community.hashi_vault.hashi_vault', 'secret/data/hello:value', token=my_token_var, url='http://myvault_url:8200', as='raw') }}"
- ansible.builtin.debug:
    msg: "This is version {{ my_secret['metadata']['version'] }} of hello:value. The secret data is {{ my_secret['data']['data']['value'] }}"

# AWS IAM authentication method
# uses Ansible standard AWS options

- name: authenticate with aws_iam_login
  ansible.builtin.debug:
    msg: "{{ lookup('community.hashi_vault.hashi_vault', 'secret/hello:value', auth_method='aws_iam_login', role_id='myroleid', profile=my_boto_profile) }}"

# JWT auth

- name: Authenticate with a JWT
  ansible.builtin.debug:
    msg: "{{ lookup('community.hashi_vault.hashi_vault', 'secret/hola:val', auth_method='jwt', role_id='myroleid', jwt='myjwt', url='https://vault:8200') }}"

# Disabling Token Validation
# Use this when your token does not have the lookup-self capability. Usually this is applied to all tokens via the default policy.
# However you can choose to create tokens without applying the default policy, or you can modify your default policy not to include it.
# When disabled, your invalid or expired token will be indistinguishable from insufficent permissions.

- name: authenticate without token validation
  ansible.builtin.debug:
    msg: "{{ lookup('community.hashi_vault.hashi_vault', 'secret/hello:value', token=my_token, token_validate=False) }}"

# "none" auth method does no authentication and does not send a token to the Vault address.
# One example of where this could be used is with a Vault agent where the agent will handle authentication to Vault.
# https://www.vaultproject.io/docs/agent

- name: authenticate with vault agent
  ansible.builtin.debug:
    msg: "{{ lookup('community.hashi_vault.hashi_vault', 'secret/hello:value', auth_method='none', url='http://127.0.0.1:8100') }}"

# Use a proxy

- name: use a proxy with login/password
  ansible.builtin.debug:
    msg: "{{ lookup('community.hashi_vault.hashi_vault', 'secret=... token=... url=https://... proxies=https://user:pass@myproxy:8080') }}"

- name: 'use a socks proxy (need some additional dependencies, see: https://requests.readthedocs.io/en/master/user/advanced/#socks )'
  ansible.builtin.debug:
    msg: "{{ lookup('community.hashi_vault.hashi_vault', 'secret=... token=... url=https://... proxies=socks5://myproxy:1080') }}"

- name: use proxies with a dict (as param)
  ansible.builtin.debug:
    msg: "{{ lookup('community.hashi_vault.hashi_vault', '...', proxies={'http': 'http://myproxy1', 'https': 'http://myproxy2'}) }}"

- name: use proxies with a dict (as param, pre-defined var)
  vars:
    prox:
      http: http://myproxy1
      https: https://myproxy2
  ansible.builtin.debug:
    msg: "{{ lookup('community.hashi_vault.hashi_vault', '...', proxies=prox }}"

- name: use proxies with a dict (as direct ansible var)
  vars:
    ansible_hashi_vault_proxies:
      http: http://myproxy1
      https: https://myproxy2
  ansible.builtin.debug:
    msg: "{{ lookup('community.hashi_vault.hashi_vault', '...' }}"

- name: use proxies with a dict (in the term string, JSON syntax)
  ansible.builtin.debug:
    msg: "{{ lookup('community.hashi_vault.hashi_vault', '... proxies={\\"http\\":\\"http://myproxy1\\",\\"https\\":\\"http://myproxy2\\"}') }}"

- name: use ansible vars to supply some options
  vars:
    ansible_hashi_vault_url: 'https://myvault:8282'
    ansible_hashi_vault_auth_method: token
  set_fact:
    secret1: "{{ lookup('community.hashi_vault.hashi_vault', 'secret/data/secret1') }}"
    secret2: "{{ lookup('community.hashi_vault.hashi_vault', 'secret/data/secret2') }}"

- name: use a custom timeout
  debug:
    msg: "{{ lookup('community.hashi_vault.hashi_vault', 'secret/data/secret1', timeout=120) }}"

- name: use a custom timeout and retry on failure 3 times (with collection retry defaults)
  vars:
    ansible_hashi_vault_timeout: 5
    ansible_hashi_vault_retries: 3
  debug:
    msg: "{{ lookup('community.hashi_vault.hashi_vault', 'secret/data/secret1') }}"

- name: retry on failure (with custom retry settings and no warnings)
  vars:
    ansible_hashi_vault_retries:
      total: 6
      backoff_factor: 0.9
      status_forcelist: [500, 502]
      allowed_methods:
        - GET
        - PUT
  debug:
    msg: "{{ lookup('community.hashi_vault.hashi_vault', 'secret/data/secret1', retry_action='warn') }}"
"""

RETURN = """
_raw:
  description:
    - secrets(s) requested
  type: list
  elements: dict
"""

import os

from ansible.errors import AnsibleError
from ansible.utils.display import Display

from ansible_collections.community.hashi_vault.plugins.lookup.__init__ import HashiVaultLookupBase
from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import HashiVaultHelper

display = Display()

HAS_HVAC = False
try:
    import hvac
    HAS_HVAC = True
except ImportError:
    HAS_HVAC = False

HAS_BOTOCORE = False
try:
    # import boto3
    import botocore
    HAS_BOTOCORE = True
except ImportError:
    HAS_BOTOCORE = False

HAS_BOTO3 = False
try:
    import boto3
    # import botocore
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


class HashiVault:
    # NOTE: the HashiVault class here is in the process of being removed, as functionality moves to shared classes

    def get_options(self, *option_names, **kwargs):
        ret = {}
        include_falsey = kwargs.get('include_falsey', False)
        for option in option_names:
            val = self.options.get(option)
            if val or include_falsey:
                ret[option] = val
        return ret

    def __init__(self, connection_options, adapter, **kwargs):
        # taking adapter during transition period
        self.adapter = adapter
        self.connection_options = connection_options

        self.options = kwargs

        self.helper = HashiVaultHelper()

        # check early that auth method is actually available
        self.auth_function = 'auth_' + self.options['auth_method']
        if not (hasattr(self, self.auth_function) and callable(getattr(self, self.auth_function))):
            raise AnsibleError(
                "Authentication method '%s' is not implemented. ('%s' member function not found)" % (self.options['auth_method'], self.auth_function)
            )

        client_args = self.connection_options.get_hvac_connection_options()

        self.client = self.helper.get_vault_client(**client_args)

    def authenticate(self):
        # We've already checked to ensure a method exists for a particular auth_method, of the form:
        #
        # auth_<method_name>
        #
        # so just call it
        getattr(self, self.auth_function)()

    def get(self):
        '''gets a secret. should always return a list'''
        secret = self.options['secret']
        field = self.options['secret_field']
        return_as = self.options['return_format']

        try:
            data = self.client.read(secret)
        except hvac.exceptions.Forbidden:
            raise AnsibleError("Forbidden: Permission Denied to secret '%s'." % secret)

        if data is None:
            raise AnsibleError("The secret '%s' doesn't seem to exist." % secret)

        if return_as == 'raw':
            return [data]

        # Check response for KV v2 fields and flatten nested secret data.
        # https://vaultproject.io/api/secret/kv/kv-v2.html#sample-response-1
        try:
            # sentinel field checks
            check_dd = data['data']['data']
            check_md = data['data']['metadata']
            # unwrap nested data
            data = data['data']
        except KeyError:
            pass

        if return_as == 'values':
            return list(data['data'].values())

        # everything after here implements return_as == 'dict'
        if not field:
            return [data['data']]

        if field not in data['data']:
            raise AnsibleError("The secret %s does not contain the field '%s'. for hashi_vault lookup" % (secret, field))

        return [data['data'][field]]

    # begin auth implementation methods
    #
    # To add new backends, 3 things should be added:
    #
    # 1. Add a new validate_auth_<method_name> method to the LookupModule, which is responsible for validating
    #    that it has the necessary options and whatever else it needs.
    #
    # 2. Update the avail_auth_methods list in the LookupModule's auth_methods() method (for now this is static).
    #
    # 3. Add a new auth_<method_name> method to this class. These implementations are faily minimal as they should
    #    already have everything they need. This is also the place to check for deprecated auth methods as hvac
    #    continues to move backends into the auth_methods class.
    #
    #    hvac is moving auth methods into the auth_methods class (added in 0.7.0)
    #    which lives in the client.auth member.
    #    https://github.com/hvac/hvac/releases/tag/v0.7.0
    #
    #    Attempting to find which backends were moved into the class when (this is primarily for warnings):
    #    0.7.0 -- github, ldap, mfa, azure?, gcp
    #    0.7.1 -- okta
    #    0.8.0 -- kubernetes
    #    0.9.0 -- azure?, radius
    #    0.9.3 -- aws
    #    0.9.6 -- userpass
    #    0.10.5 -- jwt (new)
    #    0.10.6 -- approle
    #
    def auth_token(self):
        if self.options['auth_method'] == 'token':
            self.client.token = self.options.get('token')

        if self.options.get('token_validate') and not self.client.is_authenticated():
            raise AnsibleError("Invalid Hashicorp Vault Token Specified for hashi_vault lookup.")

    def auth_userpass(self):
        params = self.get_options('username', 'password', 'mount_point')
        try:
            response = self.client.auth.userpass.login(**params)
            # must manually set the client token with userpass login
            # see https://github.com/hvac/hvac/issues/644
            self.client.token = response['auth']['client_token']
        except (NotImplementedError, AttributeError):
            display.warning("HVAC should be updated to version 0.9.6 or higher. Deprecated method 'auth_userpass' will be used.")
            self.client.auth_userpass(**params)

    def auth_ldap(self):
        params = self.get_options('username', 'password', 'mount_point')
        try:
            self.client.auth.ldap.login(**params)
        except (NotImplementedError, AttributeError):
            display.warning("HVAC should be updated to version 0.7.0 or higher. Deprecated method 'auth_ldap' will be used.")
            self.client.auth_ldap(**params)

    def auth_approle(self):
        params = self.get_options('role_id', 'secret_id', 'mount_point')
        try:
            self.client.auth.approle.login(**params)
        except (NotImplementedError, AttributeError):
            display.warning("HVAC should be updated to version 0.10.6 or higher. Deprecated method 'auth_approle' will be used.")
            self.client.auth_approle(**params)

    def auth_aws_iam_login(self):
        params = self.options['_auth_aws_iam_login_params']
        try:
            self.client.auth.aws.iam_login(**params)
        except (NotImplementedError, AttributeError):
            display.warning("HVAC should be updated to version 0.9.3 or higher. Deprecated method 'auth_aws_iam' will be used.")
            self.client.auth_aws_iam(**params)

    def auth_jwt(self):
        params = self.get_options('role_id', 'jwt', 'mount_point')
        params['role'] = params.pop('role_id')

        if 'mount_point' in params:
            params['path'] = params.pop('mount_point')

        try:
            response = self.client.auth.jwt.jwt_login(**params)
            # must manually set the client token with JWT login
            # see https://github.com/hvac/hvac/issues/644
            self.client.token = response['auth']['client_token']
        except (NotImplementedError, AttributeError):
            raise AnsibleError("JWT authentication requires HVAC version 0.10.5 or higher.")

    def auth_none(self):
        pass
    # end auth implementation methods


class LookupModule(HashiVaultLookupBase):
    def run(self, terms, variables=None, **kwargs):
        if not HAS_HVAC:
            raise AnsibleError("Please pip install hvac to use the hashi_vault lookup module.")

        ret = []

        for term in terms:
            opts = kwargs.copy()
            opts.update(self.parse_kev_term(term, first_unqualified='secret', plugin_name='hashi_vault'))
            self.set_options(direct=opts, var_options=variables)
            # TODO: remove process_deprecations() if backported fix is available (see method definition)
            self.process_deprecations()
            self.process_options()
            # passing connection_options and adapter to the HashiVault class to make transition easier
            # while the things in this class get moved to shared classes
            client = HashiVault(self.connection_options, self._options_adapter, **self._options)
            client.authenticate()
            ret.extend(client.get())

        return ret

    def process_options(self):
        '''performs deep validation and value loading for options'''

        # low preference env vars
        # doing this as a function of connection options is temporary
        # eventually each option group will handle these
        self.connection_options.process_low_preference_env_vars()

        # process connection options
        self.connection_options.process_connection_options()

        # auth methods
        self.auth_methods()

        # secret field splitter
        self.field_ops()

        # apply additional defaults
        self.apply_additional_defaults(url='http://127.0.0.1:8200')

    # begin options processing methods

    # this is a temporary method
    # https://github.com/ansible-collections/community.hashi_vault/pull/61
    # low preference env vars will be updated to take defaults into account
    def apply_additional_defaults(self, **kwargs):
        for k, v in kwargs.items():
            if self.get_option(k) is None:
                self.set_option(k, v)

    def field_ops(self):
        # split secret and field
        secret = self.get_option('secret')

        s_f = secret.rsplit(':', 1)
        self.set_option('secret', s_f[0])
        if len(s_f) >= 2:
            field = s_f[1]
        else:
            field = None
        self.set_option('secret_field', field)

    def auth_methods(self):
        # enforce and set the list of available auth methods
        # TODO: can this be read from the choices: field in documentation?
        avail_auth_methods = ['token', 'approle', 'userpass', 'ldap', 'aws_iam_login', 'jwt', 'none']
        self.set_option('avail_auth_methods', avail_auth_methods)
        auth_method = self.get_option('auth_method')

        if auth_method not in avail_auth_methods:
            raise AnsibleError(
                "Authentication method '%s' not supported. Available options are %r" % (auth_method, avail_auth_methods)
            )

        # run validator if available
        auth_validator = 'validate_auth_' + auth_method
        if hasattr(self, auth_validator) and callable(getattr(self, auth_validator)):
            getattr(self, auth_validator)(auth_method)

    # end options processing methods

    # begin auth method validators

    def validate_by_required_fields(self, auth_method, *field_names):
        missing = [field for field in field_names if not self.get_option(field)]

        if missing:
            raise AnsibleError("Authentication method %s requires options %r to be set, but these are missing: %r" % (auth_method, field_names, missing))

    def validate_auth_userpass(self, auth_method):
        self.validate_by_required_fields(auth_method, 'username', 'password')

    def validate_auth_ldap(self, auth_method):
        self.validate_by_required_fields(auth_method, 'username', 'password')

    def validate_auth_approle(self, auth_method):
        self.validate_by_required_fields(auth_method, 'role_id')

        # This lone superfluous get_option() is intentional, see:
        # https://github.com/ansible-collections/community.hashi_vault/issues/35
        self.get_option('secret_id')

    def validate_auth_token(self, auth_method):
        if auth_method == 'token':
            if not self.get_option('token') and self.get_option('token_path'):
                token_filename = os.path.join(
                    self.get_option('token_path'),
                    self.get_option('token_file')
                )
                if os.path.exists(token_filename):
                    with open(token_filename) as token_file:
                        self.set_option('token', token_file.read().strip())

            if not self.get_option('token'):
                raise AnsibleError("No Vault Token specified or discovered.")

    def validate_auth_aws_iam_login(self, auth_method):
        params = {
            'access_key': self.get_option('aws_access_key'),
            'secret_key': self.get_option('aws_secret_key'),
        }

        if self.get_option('mount_point'):
            params['mount_point'] = self.get_option('mount_point')

        if self.get_option('role_id'):
            params['role'] = self.get_option('role_id')

        if self.get_option('region'):
            params['region'] = self.get_option('region')

        if self.get_option('aws_iam_server_id'):
            params['header_value'] = self.get_option('aws_iam_server_id')

        if not (params['access_key'] and params['secret_key']):
            profile = self.get_option('aws_profile')
            if profile:
                # try to load boto profile
                if not HAS_BOTO3:
                    raise AnsibleError("boto3 is required for loading a boto profile.")
                session_credentials = boto3.session.Session(profile_name=profile).get_credentials()
            else:
                # try to load from IAM credentials
                if not HAS_BOTOCORE:
                    raise AnsibleError("botocore is required for loading IAM role credentials.")
                session_credentials = botocore.session.get_session().get_credentials()

            if not session_credentials:
                raise AnsibleError("No AWS credentials supplied or available.")

            params['access_key'] = session_credentials.access_key
            params['secret_key'] = session_credentials.secret_key
            if session_credentials.token:
                params['session_token'] = session_credentials.token

        self.set_option('_auth_aws_iam_login_params', params)

    def validate_auth_jwt(self, auth_method):
        self.validate_by_required_fields(auth_method, 'role_id', 'jwt')

    def validate_auth_none(self, auth_method):
        pass
    # end auth method validators
