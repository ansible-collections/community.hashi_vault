# -*- coding: utf-8 -*-
# Copyright (c) 2022 Isaac Wagner (@idwagner)
# Simplified BSD License (see LICENSES/BSD-2-Clause.txt or https://opensource.org/licenses/BSD-2-Clause)
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import traceback

from ansible.module_utils.basic import AnsibleModule
import hvac


def main():
    module = AnsibleModule(
        argument_spec=dict(
            url=dict(type='str', required=True),
            token=dict(type='str', required=True),
            path=dict(type='str'),
            mount_point=dict(type='str'),
        ),
    )

    p = module.params

    client = hvac.Client(url=p['url'], token=p['token'])

    extra = {}
    if p['mount_point'] is not None:
        extra['mount_point'] = p['mount_point']

    try:
        result = client.secrets.kv.v2.read_secret_metadata(path=p['path'], **extra)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())

    module.exit_json(changed=True, result=result)


if __name__ == '__main__':
    main()
