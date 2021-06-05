# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
import hvac


def main():
    module = AnsibleModule(
        argument_spec=dict(
            url=dict(type='str', required=True),
            token=dict(type='str', required=True),
            name=dict(type='str', required=True),
            policy=dict(type='raw', required=True),
        ),
    )

    p = module.params

    client = hvac.Client(url=p['url'], token=p['token'])

    client.sys.create_or_update_policy(
        name=p['name'],
        policy=p['policy'],
    )

    module.exit_json(changed=True)


if __name__ == '__main__':
    main()
