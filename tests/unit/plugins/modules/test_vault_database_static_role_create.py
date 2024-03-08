# -*- coding: utf-8 -*-
# Copyright (c) 2024 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest
import re
import json
from requests.models import Response

from ansible.module_utils.basic import missing_required_lib

from ...compat import mock
from .....plugins.modules import vault_database_static_role_create
from .....plugins.module_utils._hashi_vault_common import HashiVaultValueError


hvac = pytest.importorskip("hvac")

pytestmark = pytest.mark.usefixtures(
    "patch_ansible_module",
    "patch_authenticator",
    "patch_get_vault_client",
)


def _connection_options():
    return {
        "auth_method": "token",
        "url": "http://myvault",
        "token": "beep-boop",
    }


def _sample_options():
    return {
        "engine_mount_point": "dbmount",
    }


def _sample_role():
    return {
        "role_name": "foo",
        "connection_name": "bar",
        "db_username": "baz",
        "rotation_statements": [
            "ALTER USER \"{{name}}\" WITH PASSWORD '{{password}}';"
        ],
        "rotation_period": 86400,
    }


def response_obj():
    r = Response()
    r.status_code = 204
    return r


def _combined_options(**kwargs):
    opt = _connection_options()
    opt.update(_sample_options())
    opt.update(_sample_role())
    opt.update(kwargs)
    return opt


@pytest.fixture
def list_response(fixture_loader):
    return fixture_loader("database_static_role_create_response.json")


class TestModuleVaultDatabaseStaticRoleCreate:
    @pytest.mark.parametrize(
        "patch_ansible_module", [_combined_options()], indirect=True
    )
    @pytest.mark.parametrize(
        "exc",
        [HashiVaultValueError("throwaway msg"), NotImplementedError("throwaway msg")],
    )
    def test_vault_database_static_role_create_authentication_error(
        self, authenticator, exc, capfd
    ):
        authenticator.authenticate.side_effect = exc

        with pytest.raises(SystemExit) as e:
            vault_database_static_role_create.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)
        assert result["msg"] == "throwaway msg", "result: %r" % result

    @pytest.mark.parametrize(
        "patch_ansible_module", [_combined_options()], indirect=True
    )
    @pytest.mark.parametrize(
        "exc",
        [HashiVaultValueError("throwaway msg"), NotImplementedError("throwaway msg")],
    )
    def test_vault_database_static_role_create_auth_validation_error(
        self, authenticator, exc, capfd
    ):
        authenticator.validate.side_effect = exc

        with pytest.raises(SystemExit) as e:
            vault_database_static_role_create.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)
        assert result["msg"] == "throwaway msg"

    @pytest.mark.parametrize(
        "patch_ansible_module", [_combined_options()], indirect=True
    )
    def test_vault_database_static_role_create_return_data(
        self, patch_ansible_module, list_response, vault_client, capfd
    ):
        client = vault_client
        client.secrets.database.create_static_role.return_value = response_obj()

        with pytest.raises(SystemExit) as e:
            vault_database_static_role_create.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code == 0, "result: %r" % (result,)

        client.secrets.database.create_static_role.assert_called_once_with(
            mount_point=patch_ansible_module["engine_mount_point"],
            name=patch_ansible_module["role_name"],
            db_name=patch_ansible_module["connection_name"],
            username=patch_ansible_module["db_username"],
            rotation_statements=patch_ansible_module["rotation_statements"],
            rotation_period=patch_ansible_module["rotation_period"],
        )

        raw = list_response.copy()
        data = raw["data"]

        assert (
            result["data"] == data
        ), "module result did not match expected result:\nexpected: %r\ngot: %r" % (
            list_response,
            result,
        )

    @pytest.mark.parametrize(
        "patch_ansible_module", [_combined_options()], indirect=True
    )
    def test_vault_database_static_role_create_no_hvac(self, capfd):
        with mock.patch.multiple(
            vault_database_static_role_create,
            HAS_HVAC=False,
            HVAC_IMPORT_ERROR=None,
            create=True,
        ):
            with pytest.raises(SystemExit) as e:
                vault_database_static_role_create.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)
        assert result["msg"] == missing_required_lib("hvac")

    @pytest.mark.parametrize(
        "exc",
        [
            (
                hvac.exceptions.Forbidden,
                "",
                r"^Forbidden: Permission Denied to path \['([^']+)'\]",
            ),
            (
                hvac.exceptions.InvalidPath,
                "",
                r"^Invalid or missing path \['([^']+)/static-roles/([^']+)'\]",
            ),
        ],
    )
    @pytest.mark.parametrize(
        "patch_ansible_module",
        [[_combined_options(), "engine_mount_point"]],
        indirect=True,
    )
    @pytest.mark.parametrize("opt_engine_mount_point", ["path/1", "second/path"])
    def test_vault_database_static_role_create_vault_exception(
        self, vault_client, exc, opt_engine_mount_point, capfd
    ):

        client = vault_client
        client.secrets.database.create_static_role.side_effect = exc[0](exc[1])

        with pytest.raises(SystemExit) as e:
            vault_database_static_role_create.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)
        match = re.search(exc[2], result["msg"])
        assert match is not None, "result: %r\ndid not match: %s" % (result, exc[2])

        assert opt_engine_mount_point == match.group(1)
