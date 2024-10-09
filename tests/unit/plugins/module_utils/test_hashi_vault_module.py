# -*- coding: utf-8 -*-
# Copyright (c) 2024 Mathijs Westerhof (@mathijswesterhof)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest
from json import dumps
from ansible.module_utils import basic
from ansible.module_utils.common.text.converters import to_bytes

from ...compat import mock
from .....plugins.module_utils._hashi_vault_common import HashiVaultHVACError
from .....plugins.module_utils._hashi_vault_module import HashiVaultModule


class AnsibleFailJson(Exception):
    """Exception class to be raised by module.fail_json and caught by the test case."""
    pass


@pytest.fixture
def generate_argspec():
    return HashiVaultModule.generate_argspec(
        want_exception=dict(type='bool'),
    )


def fail_json(*args, **kwargs):
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)


class TestHashiVaultModule:

    def test_init_success(self, generate_argspec):
        """Test successful initialization of HashiVaultModule."""
        with mock.patch('ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_module.AnsibleModule') as mock_ansible_module:
            with mock.patch('ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_module.HashiVaultHelper') as mock_helper:
                basic._ANSIBLE_ARGS = to_bytes(dumps({'ANSIBLE_MODULE_ARGS': {}}))
                module = HashiVaultModule(argument_spec=generate_argspec)

                # Check if HashiVaultHelper was initialized
                mock_helper.assert_called_once()

                # Ensure that the helper, adapter, connection options, and authenticator are set correctly
                assert module.helper is not None
                assert module.adapter is not None
                assert module.connection_options is not None
                assert module.authenticator is not None

    def test_init_hvac_error(self, generate_argspec):
        """Test that HashiVaultHVACError triggers a call to fail_json."""
        with mock.patch('ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_module.HashiVaultModule.fail_json',
                        wraps=fail_json) as mock_ansible_fail:

            with mock.patch('ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_module.HashiVaultHelper',
                            side_effect=HashiVaultHVACError("Error occurred", "error_trace")) as mock_helper:
                basic._ANSIBLE_ARGS = to_bytes(dumps({'ANSIBLE_MODULE_ARGS': {}}))

                with pytest.raises(AnsibleFailJson) as exc_info:
                    # Initialize the module, which should trigger fail_json
                    module = HashiVaultModule(argument_spec=generate_argspec)

                # Optionally, assert the failure message and exception
                assert exc_info.value.args[0]['failed'] is True
                assert exc_info.value.args[0]['msg'] == "error_trace"
                assert exc_info.value.args[0]['exception'] == "Error occurred"

                mock_ansible_fail.assert_called_once_with(
                    msg="error_trace",
                    exception="Error occurred"
                )

    def test_generate_argspec(self):
        """Test that generate_argspec correctly combines connection, authentication, and extra arguments."""
        extra_args = {'extra_param': dict(type='str', required=False)}

        # Call the class method generate_argspec
        argspec = HashiVaultModule.generate_argspec(**extra_args)

        # Ensure the argument specification includes connection and authentication specs
        assert 'url' in argspec  # From HashiVaultConnectionOptions.ARGSPEC
        assert 'auth_method' in argspec  # From HashiVaultAuthenticator.ARGSPEC

        # Ensure extra parameters are included in the argument spec
        assert 'extra_param' in argspec
