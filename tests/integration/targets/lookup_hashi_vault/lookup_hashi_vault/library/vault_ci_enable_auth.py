# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
import hvac
import re


def main():
    # corresponds to https://hvac.readthedocs.io/en/stable/usage/system_backend/auth.html#enable-auth-method
    module = AnsibleModule(
        argument_spec=dict(
            url=dict(type='str', required=True),
            token=dict(type='str', required=True),
            method_type=dict(type='str', required=True),
            path=dict(type='str'),
            config=dict(type='dict'),
            kwargs=dict(type='dict'),
        ),
    )

    p = module.params

    client = hvac.Client(url=p['url'], token=p['token'])

    try:
        client.sys.enable_auth_method(
            method_type=p['method_type'],
            path=p['path'],
            config=p['config'],
            kwargs=p['kwargs'],
        )

    except hvac.exceptions.InvalidRequest as e:
        if not str(e).startswith('path is already in use'):
            raise

        path = re.sub(r'^path is already in use at ([^/]+)/.*?$', r'\1', str(e))

        methods = client.sys.list_auth_methods()['data']
        if p['path'] and p['path'] != path:
            raise

        this_method = methods[path + '/']
        if this_method['type'] != p['method_type']:
            raise

        module.warn("path in use ('%s'); retuning." % str(e))

        client.sys.tune_auth_method(
            path=path,
            config=p['config'],
            kwargs=p['kwargs'],
        )

    module.exit_json(changed=True)


if __name__ == '__main__':
    main()
