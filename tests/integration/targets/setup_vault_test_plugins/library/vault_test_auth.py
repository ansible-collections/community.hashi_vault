#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2020, Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
  lookup: vault_test_auth
  author:
    - Brian Scholer (@briantist)
  short_description: A module for testing centralized auth methods
  description: Test auth methods by performing a login to Vault and returning token information.
  extends_documentation_fragment:
    - community.hashi_vault.connection
    - community.hashi_vault.auth
  options:
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


# this module is for running tests only; no_log can interfere with return values
# and/or  makie it harder to troubleshoot test failures.
def strip_no_log(spec):
    for key in list(spec.keys()):
        if 'no_log' in spec[key]:
            spec[key]['no_log'] = False


def run_module():
    argspec = HashiVaultModule.generate_argspec(
        want_exception=dict(type='bool'),
    )

    strip_no_log(argspec)

    module = HashiVaultModule(
        argument_spec=argspec,
        supports_check_mode=False
    )

    options = module.adapter

    module.connection_options.process_connection_options()
    client_args = module.connection_options.get_hvac_connection_options()
    client = module.helper.get_vault_client(**client_args)

    err = msg = response = None
    try:
        try:
            module.authenticator.validate()
            response = module.authenticator.authenticate(client)
        except NotImplementedError as e:
            module.fail_json(msg=str(e), exception=e)
    except Exception as e:
        msg = str(e)
        if options.get_option('want_exception'):
            err = dictify(e)
        else:
            module.fail_json(msg=msg, exception=e)

    rob = {
        'login': response,
        'failed': False,
        'inner': {'failed': False}
    }

    if err is not None:
        rob['inner']['failed'] = True
        rob['exception'] = err
        rob['msg'] = msg

    module.exit_json(**rob)


def main():
    run_module()


if __name__ == '__main__':
    main()
