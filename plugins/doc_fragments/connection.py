# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    DOCUMENTATION = r'''
    options:
      url:
        description:
          - URL to the Vault service.
          - If not specified by any other means, the value of the C(VAULT_ADDR) environment variable will be used.
          - If C(VAULT_ADDR) is also not defined then a default of C(http://127.0.0.1:8200) will be used.
        env:
          - name: ANSIBLE_HASHI_VAULT_ADDR
            version_added: '0.2.0'
        ini:
          - section: lookup_hashi_vault
            key: url
      proxies:
        description:
          - URL(s) to the proxies used to access the Vault service.
          - It can be a string or a dict.
          - If it's a dict, provide the scheme (eg. C(http) or C(https)) as the key, and the URL as the value.
          - If it's a string, provide a single URL that will be used as the proxy for both C(http) and C(https) schemes.
          - A string that can be interpreted as a dictionary will be converted to one (see examples).
          - You can specify a different proxy for HTTP and HTTPS resources.
          - If not specified, L(environment variables from the Requests library,https://requests.readthedocs.io/en/master/user/advanced/#proxies) are used.
        env:
          - name: ANSIBLE_HASHI_VAULT_PROXIES
        ini:
          - section: lookup_hashi_vault
            key: proxies
        type: raw
        version_added: '1.1.0'
      ca_cert:
        description: Path to certificate to use for authentication.
        aliases: [ cacert ]
      validate_certs:
        description:
          - Controls verification and validation of SSL certificates, mostly you only want to turn off with self signed ones.
          - Will be populated with the inverse of C(VAULT_SKIP_VERIFY) if that is set and I(validate_certs) is not explicitly provided.
          - Will default to C(true) if neither I(validate_certs) or C(VAULT_SKIP_VERIFY) are set.
        type: boolean
      namespace:
        description:
          - Vault namespace where secrets reside. This option requires HVAC 0.7.0+ and Vault 0.11+.
          - Optionally, this may be achieved by prefixing the authentication mount point and/or secret path with the namespace
            (e.g C(mynamespace/secret/mysecret)).
          - If environment variable C(VAULT_NAMESPACE) is set, its value will be used last among all ways to specify I(namespace).
        env:
          - name: ANSIBLE_HASHI_VAULT_NAMESPACE
            version_added: '0.2.0'
        ini:
          - section: lookup_hashi_vault
            key: namespace
            version_added: '0.2.0'
    '''
