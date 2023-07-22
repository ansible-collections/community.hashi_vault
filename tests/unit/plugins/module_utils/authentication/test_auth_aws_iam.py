# -*- coding: utf-8 -*-
# Copyright (c) 2021 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible_collections.community.hashi_vault.tests.unit.compat import mock

from ansible_collections.community.hashi_vault.plugins.module_utils._auth_method_aws_iam import (
    HashiVaultAuthMethodAwsIam,
)

from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import (
    HashiVaultAuthMethodBase,
    HashiVaultValueError,
)


@pytest.fixture
def option_dict():
    return {
        'auth_method': 'aws_iam',
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
def aws_session_token():
    return 'session-token'


@pytest.fixture
def auth_aws_iam(adapter, warner, deprecator):
    return HashiVaultAuthMethodAwsIam(adapter, warner, deprecator)


@pytest.fixture
def aws_iam_login_response(fixture_loader):
    return fixture_loader('aws_iam_login_response.json')


@pytest.fixture
def boto_mocks(aws_access_key, aws_secret_key, aws_session_token):
    class botocore_profile_not_found(Exception):
        pass

    credentials = mock.MagicMock(access_key=aws_access_key, secret_key=aws_secret_key, token=aws_session_token)
    mock_session = mock.MagicMock(get_credentials=mock.MagicMock(return_value=credentials))

    def _Session(profile_name):
        if profile_name == 'missing_profile':
            raise botocore_profile_not_found

        return mock_session

    boto3 = mock.MagicMock()
    boto3.session.Session = mock.MagicMock(side_effect=_Session)

    botocore = mock.MagicMock()
    botocore.exceptions.ProfileNotFound = botocore_profile_not_found

    return mock.MagicMock(
        botocore=botocore,
        boto3=boto3,
        session=mock_session,
        credentials=credentials
    )


class TestAuthAwsIam(object):

    def test_auth_aws_iam_is_auth_method_base(self, auth_aws_iam):
        assert isinstance(auth_aws_iam, HashiVaultAuthMethodAwsIam)
        assert issubclass(HashiVaultAuthMethodAwsIam, HashiVaultAuthMethodBase)

    @pytest.mark.parametrize('aws_security_token', [None, 'session-token'], ids=lambda x: 'aws_security_token=%s' % x)
    @pytest.mark.parametrize('region', [None, 'ap-northeast-1'], ids=lambda x: 'region=%s' % x)
    @pytest.mark.parametrize('aws_iam_server_id', [None, 'server-id'], ids=lambda x: 'aws_iam_server_id=%s' % x)
    @pytest.mark.parametrize('role_id', [None, 'vault-role'], ids=lambda x: 'role_id=%s' % x)
    @pytest.mark.parametrize('mount_point', [None, 'other'], ids=lambda x: 'mount_point=%s' % x)
    def test_auth_aws_iam_validate(
        self, auth_aws_iam, adapter, aws_access_key, aws_secret_key, aws_security_token,
        region, aws_iam_server_id, role_id, mount_point
    ):
        adapter.set_options(
            aws_access_key=aws_access_key, aws_secret_key=aws_secret_key, aws_security_token=aws_security_token,
            region=region, aws_iam_server_id=aws_iam_server_id, role_id=role_id, mount_point=mount_point
        )

        auth_aws_iam.validate()

        login_params = auth_aws_iam._auth_aws_iam_login_params

        assert login_params['access_key'] == aws_access_key
        assert login_params['secret_key'] == aws_secret_key

        assert (aws_security_token is None and 'session_token' not in login_params) or login_params['session_token'] == aws_security_token
        assert (mount_point is None and 'mount_point' not in login_params) or login_params['mount_point'] == mount_point
        assert (role_id is None and 'role' not in login_params) or login_params['role'] == role_id
        assert (region is None and 'region' not in login_params) or login_params['region'] == region
        assert (aws_iam_server_id is None and 'header_value' not in login_params) or login_params['header_value'] == aws_iam_server_id

    @pytest.mark.parametrize('use_token', [True, False], ids=lambda x: 'use_token=%s' % x)
    @pytest.mark.parametrize('mount_point', [None, 'other'], ids=lambda x: 'mount_point=%s' % x)
    @pytest.mark.parametrize('aws_security_token', [None, 'session-token'], ids=lambda x: 'aws_security_token=%s' % x)
    @pytest.mark.parametrize('region', [None, 'ap-northeast-1'], ids=lambda x: 'region=%s' % x)
    @pytest.mark.parametrize('aws_iam_server_id', [None, 'server-id'], ids=lambda x: 'aws_iam_server_id=%s' % x)
    @pytest.mark.parametrize('role_id', [None, 'vault-role'], ids=lambda x: 'role_id=%s' % x)
    def test_auth_aws_iam_authenticate(
        self, auth_aws_iam, client, adapter, aws_access_key, aws_secret_key, aws_security_token,
        region, aws_iam_server_id, role_id, mount_point, use_token, aws_iam_login_response
    ):
        adapter.set_options(
            aws_access_key=aws_access_key, aws_secret_key=aws_secret_key, aws_security_token=aws_security_token,
            region=region, aws_iam_server_id=aws_iam_server_id, role_id=role_id, mount_point=mount_point
        )

        auth_aws_iam.validate()

        expected_login_params = auth_aws_iam._auth_aws_iam_login_params.copy()

        with mock.patch.object(client.auth.aws, 'iam_login', return_value=aws_iam_login_response) as aws_iam_login:
            response = auth_aws_iam.authenticate(client, use_token=use_token)
            aws_iam_login.assert_called_once_with(use_token=use_token, **expected_login_params)

        assert response['auth']['client_token'] == aws_iam_login_response['auth']['client_token']

    def test_auth_aws_iam_validate_no_creds_no_boto(self, auth_aws_iam, mock_import_error):
        with mock_import_error('botocore', 'boto3'):
            with pytest.raises(HashiVaultValueError, match=r'boto3 is required for loading a profile or IAM role credentials'):
                auth_aws_iam.validate()

    @pytest.mark.parametrize('profile', ['my_aws_profile', None])
    def test_auth_aws_iam_validate_inferred_creds(self, auth_aws_iam, boto_mocks, adapter, profile, aws_access_key, aws_secret_key, aws_session_token):
        adapter.set_option('aws_profile', profile)

        botocore = boto_mocks.botocore
        boto3 = boto_mocks.boto3

        with mock.patch.dict('sys.modules', {'botocore': botocore, 'boto3': boto3}):
            auth_aws_iam.validate()

        params = auth_aws_iam._auth_aws_iam_login_params

        boto3.session.Session.assert_called_once_with(profile_name=profile)

        assert params['access_key'] == aws_access_key
        assert params['secret_key'] == aws_secret_key
        assert params['session_token'] == aws_session_token

    @pytest.mark.parametrize('profile', ['missing_profile'])
    def test_auth_aws_iam_validate_missing_profile(self, auth_aws_iam, boto_mocks, adapter, profile):
        adapter.set_option('aws_profile', profile)

        botocore = boto_mocks.botocore
        boto3 = boto_mocks.boto3

        with mock.patch.dict('sys.modules', {'botocore': botocore, 'boto3': boto3}):
            with pytest.raises(HashiVaultValueError, match="The AWS profile '%s' was not found" % profile):
                auth_aws_iam.validate()

    @pytest.mark.parametrize('profile', ['my_aws_profile', None])
    def test_auth_aws_iam_validate_no_inferred_creds_found(self, auth_aws_iam, boto_mocks, adapter, profile):
        adapter.set_option('aws_profile', profile)

        botocore = boto_mocks.botocore
        boto3 = boto_mocks.boto3

        with mock.patch.dict('sys.modules', {'botocore': botocore, 'boto3': boto3}):
            with mock.patch.object(boto_mocks.session, 'get_credentials', return_value=None):
                with pytest.raises(HashiVaultValueError, match=r'No AWS credentials supplied or available'):
                    auth_aws_iam.validate()
