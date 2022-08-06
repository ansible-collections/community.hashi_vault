# (c) 2020, Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
  name: vault_test_connection
  author:
    - Brian Scholer (@briantist)
  short_description: A plugin for testing connection to Vault
  description: Test connection to Vault and return useful information.
  extends_documentation_fragment:
    - community.hashi_vault.connection
    - community.hashi_vault.connection.plugins
  options:
    want_client:
      type: bool
      default: False
      vars:
        - name: vault_test_connection_want_client
    want_args:
      type: bool
      default: False
      vars:
        - name: vault_test_connection_want_args
    want_exception:
      type: bool
      default: False
      vars:
        - name: vault_test_connection_want_exception
"""
import json
from ansible.utils.display import Display

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
    _retry_count = 0

    def _generate_retry_callback(self, retry_action):
        '''returns a Retry callback function for plugins'''

        original = super(LookupModule, self)._generate_retry_callback(retry_action)

        def _on_retry(retry_obj):
            if retry_obj.total > 0:
                self._retry_count += 1

            original(retry_obj)

        return _on_retry

    def run(self, terms, variables=None, **kwargs):
        options = self._options_adapter
        err = status = msg = None
        ret = []

        for term in terms:
            opts = kwargs.copy()
            self.set_options(direct=opts, var_options=variables)
            self.connection_options.process_connection_options()
            client_args = self.connection_options.get_hvac_connection_options()
            client = self.helper.get_vault_client(**client_args)

            try:
                status = client.sys.read_health_status(method='GET')
            except Exception as e:
                if options.get_option('want_exception'):
                    err = dictify(e)
                    msg = str(e)
                else:
                    raise

            rob = {
                'retries': self._retry_count,
                'status': status,
                'failed': False,
            }

            if options.get_option('want_client'):
                rob['client'] = dictify(client)

            if options.get_option('want_args'):
                rob['args'] = dictify(client_args)

            if err is not None:
                rob['failed'] = True
                rob['exception'] = err
                rob['msg'] = msg

            ret.extend([rob])

        return ret
