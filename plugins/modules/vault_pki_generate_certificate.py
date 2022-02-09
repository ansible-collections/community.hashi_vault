#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2022, Florent David <florent.david@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
  module: vault_pki_generate_certificate
  version_added: 2.3.0
  author:
    - Florent David <florent.david@gmail.com>
  short_description: Generates a new set of credentials (private key and certificate) using HashiCorp Vault PKI
  requirements:
    - C(hvac) (L(Python library,https://hvac.readthedocs.io/en/stable/overview.html))
    - For detailed requirements, see R(the collection requirements page,ansible_collections.community.hashi_vault.docsite.user_guide.requirements).
  description:
    - Generates a new set of credentials (private key and certificate) based on a role named and depending PKI's mount point.
  seealso:
    - name: Hashicorp Vault PKI Secrets Engine API
      description: API documentation for the Hashicorp Vault PKI secrets engine.
      link: https://www.vaultproject.io/api/secret/pki#generate-certificate
    - name: HVAC library reference
      description: Reference of the HVAC library about PKI engine.
      link: https://hvac.readthedocs.io/en/stable/usage/secrets_engines/pki.html#generate-certificate
  extends_documentation_fragment:
    - community.hashi_vault.connection
    - community.hashi_vault.auth
  options:
    alt_names:
      description:
        - Specifies requested Subject Alternative Names.
        - These can be host names or email addresses; they will be parsed into their respective fields.
        - If any requested names do not match role policy, the entire request will be denied.
      type: list
    common_name:
      description:
        - Specifies the requested CN for the certificate.
        - If the CN is allowed by role policy, it will be issued.
      type: str
      required: true
    exclude_cn_from_sans:
      description:
        - If true, the given I(common_name) will not be included in DNS or Email Subject Alternate Names (as appropriate).
        - Useful if the CN is not a hostname or email address, but is instead some human-readable identifier.
      type: bool
    format:
      description:
        - Specifies the format for returned data.
        - Can be C(pem), C(der), or C(pem_bundle).
        - If C(der), the output is base64 encoded.
        - >-
          If C(pem_bundle), the C(certificate) field will contain the private key and certificate, concatenated; if the issuing CA is not a Vault-derived
          self-signed root, this will be included as well.
      type: str
      choices: [pem, der, pem_bundle]
      default: pem
    ip_sans:
      description:
        - Specifies requested IP Subject Alternative Names.
        - Only valid if the role allows IP SANs (which is the default).
      type: list
    name:
      description:
        - Specifies the name of the role to create the certificate against.
      type: str
      required: true
    other_sans:
      description:
        - Specifies custom OID/UTF8-string SANs.
        - These must match values specified on the role in C(allowed_other_sans).
        - The format is the same as OpenSSL: C(<oid>;<type>:<value>) where the only current valid type is C(UTF8).
      type: list
    path:
      description:
        - Specify the mount point used by the PKI engine.
      type: str
      default: pki
    private_key_format:
      description:
        - Specifies the format for marshaling the private key.
        - Defaults to C(der) which will return either base64-encoded DER or PEM-encoded DER, depending on the value of I(format).
        - The other option is C(pkcs8) which will return the key marshalled as PEM-encoded PKCS8.
      type: str
      choices: [der, pkcs8]
      default: der
    ttl:
      description:
        - Specifies requested Time To Live.
        - Cannot be greater than the role's C(max_ttl) value.
        - If not provided, the role's C(ttl) value will be used.
        - Note that the role values default to system values if not explicitly set.
      type: str
    uri_sans:
      description:
        - Specifies the requested URI Subject Alternative Names.
      type: list
"""

EXAMPLES = """
- name: Login and use the resulting token
  community.hashi_vault.vault_login:
    url: https://localhost:8200
    auth_method: ldap
    username: "john.doe"
    password: "{{ user_passwd }}"
  register: login_data

- name: Generate a certificate with a existing token
  community.hashi_vault.vault_pki_generate_certificate:
    name: test.example.org
    common_name: test.example.org
    ttl: 8760h
    alt_names:
      - test2.example.org
      - test3.example.org
    url: https://vault:8201
    auth_method: token
    token: "{{ login_data.login.auth.client_token }}"
  register: cert_data

- name: Display generated certificate
  debug:
    msg: "{{ cert_data.data.data.certificate }}"
"""

RETURN = """
data:
  description: Information about newly generated certificate
  returned: success
  type: complex
  contains:
    lease_id:
      description: Vault lease attached to certificate
      returned: success
      type: string
      sample: pki/issue/test/7ad6cfa5-f04f-c62a-d477-f33210475d05
    renewable:
      description: Is certificate renewable ?
      returned: success
      type: boolean
      sample: false
    lease_duration:
      description: Vault lease duration
      returned: success
      type: int
      sample: 21600
    data:
      description: Payload
      returned: success
      type: complex
      contains:
        certificate:
          description: Newly generated X509 certificate
          returned: success
          type: string
          sample: "-----BEGIN CERTIFICATE-----...-----END CERTIFICATE-----"
        issuing_ca:
          description: Certificate Authority X509 certificate
          returned: success
          type: string
          sample: "-----BEGIN CERTIFICATE-----...-----END CERTIFICATE-----"
        ca_chain:
          description: Linked list of Certificate Authorities X509 certificates
          returned: success
          type: list
          sample: ["-----BEGIN CERTIFICATE-----...-----END CERTIFICATE-----"]
        private_key:
          description: Private key used to generate certificate
          returned: success
          type: string
          sample: "-----BEGIN RSA PRIVATE KEY-----...-----END RSA PRIVATE KEY-----"
        private_key_type:
          description: Private key algorithm
          returned: success
          type: string
          sample: rsa
        serial_number:
          description: Certificate's serial number
          returned: success
          type: string
          sample: 39:dd:2e:90:b7:23:1f:8d:d3:7d:31:c5:1b:da:84:d0:5b:65:31:58
    warning:
      description: Warning throw during generation
      returned: success
      type: string
"""

import traceback

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_native

from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_module import HashiVaultModule
from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import HashiVaultValueError

HAS_HVAC = False
try:
    import hvac
    from hvac.api.secrets_engines.pki import DEFAULT_MOUNT_POINT
    HAS_HVAC = True
except ImportError:
    HAS_HVAC = False


def run_module():
    if not HAS_HVAC:
        raise AnsibleError("Please pip install hvac to use the hashi_vault modules.")

    argspec = HashiVaultModule.generate_argspec(
        name=dict(type='str', required=True),
        common_name=dict(type='str', required=True),
        alt_names=dict(type='list', elements='str', required=False, default=[]),
        ip_sans=dict(type='list', elements='str', required=False, default=[]),
        uri_sans=dict(type='list', elements='str', required=False, default=[]),
        other_sans=dict(type='list', elements='str', required=False, default=[]),
        ttl=dict(type='str', required=False, default=None),
        format=dict(type='str', required=False, choices=['pem', 'der', 'pem_bundle'], default='pem'),
        private_key_format=dict(type='str', required=False, choices=['der', 'pkcs8'], default='der'),
        exclude_cn_from_sans=dict(type='bool', required=False, default=False),
        path=dict(type='str', required=False, default=DEFAULT_MOUNT_POINT)
    )

    module = HashiVaultModule(
        argument_spec=argspec,
        supports_check_mode=True
    )

    name = module.params.get('name')
    common_name = module.params.get('common_name')
    path = module.params.get('path')

    extra_params = {
        'alt_names': ','.join(module.params.get('alt_names')),
        'ip_sans': ','.join(module.params.get('ip_sans')),
        'uri_sans': ','.join(module.params.get('uri_sans')),
        'other_sans': ','.join(module.params.get('other_sans')),
        'ttl': module.params.get('ttl'),
        'format': module.params.get('format'),
        'private_key_format': module.params.get('private_key_format'),
        'exclude_cn_from_sans': module.params.get('exclude_cn_from_sans')
    }

    module.connection_options.process_connection_options()
    client_args = module.connection_options.get_hvac_connection_options()
    client = module.helper.get_vault_client(**client_args)

    try:
        module.authenticator.validate()
        module.authenticator.authenticate(client)
    except (NotImplementedError, HashiVaultValueError) as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    try:
        data = client.secrets.pki.generate_certificate(name, common_name,
                                                       extra_params=extra_params, mount_point=path)
    except hvac.exceptions.VaultError as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    # generate_certificate is a write operation which always return a new certificate
    module.exit_json(changed=True, data=data)


def main():
    run_module()


if __name__ == '__main__':
    main()
