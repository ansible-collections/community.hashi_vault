# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# Simplified BSD License (see LICENSES/BSD-2-Clause.txt or https://opensource.org/licenses/BSD-2-Clause)
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
import hvac


def main():
    module = AnsibleModule(
        argument_spec=dict(
            url=dict(type='str', required=True),
            token=dict(type='str', required=True),
            no_default_policy=dict(type='bool', default=False),
            policies=dict(type='list'),
            ttl=dict(type=str, default='1h'),
        ),
    )

    p = module.params

    client = hvac.Client(url=p['url'], token=p['token'])

    result = client.auth.token.create(
        policies=p['policies'],
        no_default_policy=p.get('no_default_policy'),
        ttl=p.get('ttl'),
    )

    module.exit_json(changed=True, result=result)


if __name__ == '__main__':
    main()
