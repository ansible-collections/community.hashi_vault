# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# Simplified BSD License (see LICENSES/BSD-2-Clause.txt or https://opensource.org/licenses/BSD-2-Clause)
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
import hvac
import json


def main():
    module = AnsibleModule(
        argument_spec=dict(
            url=dict(type='str', required=True),
            token=dict(type='str', required=True),
            path=dict(type='str', required=True),
            data=dict(type='dict', required=True),
        ),
    )

    p = module.params

    client = hvac.Client(url=p['url'], token=p['token'])

    result = client.write(path=p['path'], **p['data'])

    dictified = json.loads(
        json.dumps(
            result,
            skipkeys=True,
            default=lambda o: getattr(o, '__dict__', str(o)),
        )
    )

    module.exit_json(changed=True, result=dictified)


if __name__ == '__main__':
    main()
