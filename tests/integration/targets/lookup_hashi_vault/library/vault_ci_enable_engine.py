# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
import hvac


def main():
    # corresponds to https://hvac.readthedocs.io/en/stable/usage/system_backend/mount.html#enable-secrets-engine
    module = AnsibleModule(
        argument_spec=dict(
            url=dict(type='str', required=True),
            token=dict(type='str', required=True),
            backend_type=dict(type='str', required=True),
            path=dict(type='str'),
            config=dict(type='dict'),
            options=dict(type='dict'),
            kwargs=dict(type='dict'),
        ),
    )

    p = module.params

    client = hvac.Client(url=p['url'], token=p['token'])

    try:
        client.sys.enable_secrets_engine(
            backend_type=p['backend_type'],
            path=p['path'],
            config=p['config'],
            options=p['options'],
            kwargs=p['kwargs'],
        )

    except hvac.exceptions.InvalidRequest as e:
        if not str(e).startswith('path is already in use'):
            raise

        engines = client.sys.list_mounted_secrets_engines()['data']
        this_engine = engines[p['path'].strip('/') + '/']
        if this_engine['type'] != p['backend_type']:
            raise

        module.warn("path '%s' of type '%s' already exists; retuning." % (p['path'], this_engine['type']))

        client.sys.tune_mount_configuration(
            path=p['path'],
            config=p['config'],
            options=p['options'],
            kwargs=p['kwargs'],
        )

    module.exit_json(changed=True)


if __name__ == '__main__':
    main()
