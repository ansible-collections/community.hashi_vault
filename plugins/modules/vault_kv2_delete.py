
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
module: vault_kv2_get
'''


import traceback

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import missing_required_lib

from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_module import HashiVaultModule
from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import HashiVaultValueError

try:
    import hvac
except ImportError:
    HAS_HVAC = False
    HVAC_IMPORT_ERROR = traceback.format_exc()
else:
    HVAC_IMPORT_ERROR = None
    HAS_HVAC = True

def run_module():


    argspec = HashiVaultModule.generate_argspec(
        engine_mount_point=dict(type='str', default='kv'),
        path=dict(type='str', required=True)
    )

    module = HashiVaultModule(
        argument_spec=argspec,
        supports_check_mode=True
    )

    if not HAS_HVAC:
        module.fail_json(
            msg=missing_required_lib('hvac'),
            exception=HVAC_IMPORT_ERROR
        )

    engine_mount_point = module.params.get('engine_mount_point')
    path = module.params.get('path')

    module.connection_options.process_connection_options()
    client_args = module.connection_options.get_hvac_connection_options()
    client = module.helper.get_vault_client(**client_args)

    try:
        module.authenticator.validate()
        module.authenticator.authenticate(client)
    except (NotImplementedError, HashiVaultValueError) as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    try:
        raw = client.secrets.kv.v2.delete_latest_version_of_secret(path=path, mount_point=engine_mount_point)
    except hvac.exceptions.Forbidden as e:
        module.fail_json(msg="Forbidden: Permission Denied to path ['%s']." % path, exception=traceback.format_exc())

    module.exit_json(changed=True, response_code=raw.status_code)

def main():
    run_module()


if __name__ == '__main__':
    main()
