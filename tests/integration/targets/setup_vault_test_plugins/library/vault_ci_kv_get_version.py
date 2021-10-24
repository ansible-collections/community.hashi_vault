# -*- coding: utf-8 -*-
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
import hvac


def main():
    """
    We can't read the a version of a kv-v2 secret using vault_ci_read.
    """
    module = AnsibleModule(
        argument_spec=dict(
            url=dict(type='str', required=True),
            token=dict(type='str', required=True),
            path=dict(type='str', required=True),
            version=dict(type='int', required=True),
            mount_point=dict(type='str')
        ),
    )

    p = module.params

    client = hvac.Client(url=p['url'], token=p['token'])

    extra = {}
    if p['mount_point'] is not None:
        extra['mount_point'] = p['mount_point']

    client.secrets.kv.v2.read_secret_version(
        path=p['path'],
        version=p['version'],
        **extra
    )

    module.exit_json(changed=True)


if __name__ == '__main__':
    main()
