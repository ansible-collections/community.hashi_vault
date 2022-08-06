# (c) 2020, Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
  name: vault_test_auth
  author:
    - Brian Scholer (@briantist)
  short_description: A plugin for testing centralized auth methods
  description: Test auth methods by performing a login to Vault and returning token information.
  extends_documentation_fragment:
    - community.hashi_vault.connection
    - community.hashi_vault.connection.plugins
    - community.hashi_vault.auth
    - community.hashi_vault.auth.plugins
  options:
    want_exception:
      type: bool
      default: False
      vars:
        - name: vault_test_auth_want_exception
"""
import json
from ansible.utils.display import Display
from ansible.errors import AnsibleError

from ansible_collections.community.hashi_vault.plugins.plugin_utils._hashi_vault_lookup_base import HashiVaultLookupBase

display = Display()


def dictify(thing):
    return json.loads(
        json.dumps(
            thing,
            skipkeys=True,
            default=lambda o: getattr(o, '__dict__', str(o)),
        )
    )


class LookupModule(HashiVaultLookupBase):
    def run(self, terms, variables=None, **kwargs):
        options = self._options_adapter
        err = response = msg = None
        ret = []

        if len(terms) != 0:
            raise AnsibleError("Don't use a term string with this.")

        opts = kwargs.copy()
        self.set_options(direct=opts, var_options=variables)
        self.connection_options.process_connection_options()
        client_args = self.connection_options.get_hvac_connection_options()
        client = self.helper.get_vault_client(**client_args)

        try:
            try:
                self.authenticator.validate()
                response = self.authenticator.authenticate(client)
            except NotImplementedError as e:
                raise AnsibleError(e)
        except Exception as e:
            if options.get_option('want_exception'):
                err = dictify(e)
                msg = str(e)
            else:
                raise

        rob = {
            'login': response,
            'failed': False,
        }

        if err is not None:
            rob['failed'] = True
            rob['exception'] = err
            rob['msg'] = msg

        ret.extend([rob])

        return ret
