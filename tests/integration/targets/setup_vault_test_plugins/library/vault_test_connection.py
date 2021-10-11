#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2020, Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
  lookup: vault_test_connection
  author:
    - Brian Scholer (@briantist)
  short_description: A module for testing connection to Vault
  description: Test connection to Vault and return useful information.
  extends_documentation_fragment:
    - community.hashi_vault.connection
  options:
    want_client:
      type: bool
      default: False
    want_args:
      type: bool
      default: False
    want_exception:
      type: bool
      default: False
"""
import json

from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_module import HashiVaultModule


def dictify(thing):
    return json.loads(
        json.dumps(
            thing,
            skipkeys=True,
            default=lambda o: getattr(o, '__dict__', str(o)),
        )
    )


def run_module():
    this = dict(_retry_count=0)

    argspec = HashiVaultModule.generate_argspec(
        want_client=dict(type='bool'),
        want_args=dict(type='bool'),
        want_exception=dict(type='bool'),
    )

    def _generate_retry_callback(retry_action):
        '''returns a Retry callback function for plugins'''
        dummy = HashiVaultModule(argument_spec=argspec)
        original = dummy._generate_retry_callback(retry_action)

        def _on_retry(retry_obj):
            if retry_obj.total > 0:
                this['_retry_count'] += 1

            original(retry_obj)

        return _on_retry

    module = HashiVaultModule(
        hashi_vault_custom_retry_callback=_generate_retry_callback,
        argument_spec=argspec,
        supports_check_mode=False
    )

    options = module.adapter
    err = status = msg = None

    module.connection_options.process_connection_options()
    client_args = module.connection_options.get_hvac_connection_options()
    client = module.helper.get_vault_client(**client_args)

    try:
        status = client.sys.read_health_status(method='GET')
    except Exception as e:
        if options.get_option_default('want_exception'):
            err = dictify(e)
            msg = str(e)
        else:
            raise

    rob = {
        'retries': this['_retry_count'],
        'status': status,
        'failed': False,
        'inner': {'failed': False}
    }

    if options.get_option_default('want_client'):
        rob['client'] = dictify(client)

    if options.get_option_default('want_args'):
        rob['args'] = dictify(client_args)

    if err is not None:
        rob['inner']['failed'] = True
        rob['exception'] = err
        rob['msg'] = msg

    module.exit_json(**rob)


def main():
    run_module()


if __name__ == '__main__':
    main()
