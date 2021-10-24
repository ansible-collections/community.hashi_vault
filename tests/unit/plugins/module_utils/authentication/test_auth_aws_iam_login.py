# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible_collections.community.hashi_vault.tests.unit.compat import mock

from ansible_collections.community.hashi_vault.plugins.module_utils._auth_method_aws_iam_login import (
    HashiVaultAuthMethodAwsIamLogin,
)

from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import (
    HashiVaultAuthMethodBase,
    HashiVaultValueError,
)


@pytest.fixture
def option_dict():
    return {
        'auth_method': 'aws',
        'aws_access_key': None,
        'aws_secret_key': None,
        'aws_profile': None,
        'aws_security_token': None,
        'region': None,
        'aws_iam_server_id': None,
        'role_id': None,
        'mount_point': None,
    }


@pytest.fixture
def aws_access_key():
    return 'access-key'


@pytest.fixture
def aws_secret_key():
    return 'secret-key'


@pytest.fixture
def auth_aws_iam_login(adapter, warner):
    return HashiVaultAuthMethodAwsIamLogin(adapter, warner)


# TODO: these tests aren't complete but are doing some basic checking that the parameters are being passed correctly.
# They will be filled out eventually. See also:
# - https://github.com/ansible-collections/community.hashi_vault/issues/160 (this issue is caught by these tests)
# - https://github.com/ansible-collections/community.hashi_vault/issues/118
class TestAuthAwsIamLogin(object):

    def test_auth_aws_iam_login_is_auth_method_base(self, auth_aws_iam_login):
        assert isinstance(auth_aws_iam_login, HashiVaultAuthMethodAwsIamLogin)
        assert issubclass(HashiVaultAuthMethodAwsIamLogin, HashiVaultAuthMethodBase)

    @pytest.mark.parametrize('aws_security_token', [None, 'session-token'], ids=lambda x: 'aws_security_token=%s' % x)
    @pytest.mark.parametrize('region', [None, 'ap-northeast-1'], ids=lambda x: 'region=%s' % x)
    @pytest.mark.parametrize('aws_iam_server_id', [None, 'server-id'], ids=lambda x: 'aws_iam_server_id=%s' % x)
    @pytest.mark.parametrize('role_id', [None, 'vault-role'], ids=lambda x: 'role_id=%s' % x)
    @pytest.mark.parametrize('mount_point', [None, 'other'], ids=lambda x: 'mount_point=%s' % x)
    def test_auth_iam_login_validate(
        self, auth_aws_iam_login, adapter, aws_access_key, aws_secret_key,
        aws_security_token, region, aws_iam_server_id, role_id, mount_point
    ):
        adapter.set_options(
            aws_access_key=aws_access_key, aws_secret_key=aws_secret_key, aws_security_token=aws_security_token,
            region=region, aws_iam_server_id=aws_iam_server_id, role_id=role_id, mount_point=mount_point
        )

        auth_aws_iam_login.validate()

        login_params = auth_aws_iam_login._auth_aws_iam_login_params

        assert login_params['access_key'] == aws_access_key
        assert login_params['secret_key'] == aws_secret_key

        assert (aws_security_token is None and 'session_token' not in login_params) or login_params['session_token'] == aws_security_token
        assert (mount_point is None and 'mount_point' not in login_params) or login_params['mount_point'] == mount_point
        assert (role_id is None and 'role' not in login_params) or login_params['role'] == role_id
        assert (region is None and 'region' not in login_params) or login_params['region'] == region
        assert (aws_iam_server_id is None and 'header_value' not in login_params) or login_params['header_value'] == aws_iam_server_id
