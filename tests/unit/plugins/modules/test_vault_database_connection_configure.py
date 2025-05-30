# -*- coding: utf-8 -*-
# Copyright (c) 2024 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest
import re
import json

from .....plugins.modules import vault_database_connection_configure
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


def _sample_connection():
    return {
        "connection_name": "foo",
        "plugin_name": "bar",
        "allowed_roles": [
            "baz",
        ],
        "connection_url": "postgresql://{{'{{username}}'}}:{{'{{password}}'}}@postgres:5432/postgres?sslmode=disable",
        "connection_username": "SomeUser",
        "connection_password": "SomePass",
    }


def _combined_options(**kwargs):
    opt = _connection_options()
    opt.update(_sample_options())
    opt.update(_sample_connection())
    opt.update(kwargs)
    return opt


class TestModuleVaultDatabaseConnectionConfigure:
    @pytest.mark.parametrize(
        "patch_ansible_module", [_combined_options()], indirect=True
    )
    @pytest.mark.parametrize(
        "exc",
        [HashiVaultValueError("throwaway msg"), NotImplementedError("throwaway msg")],
    )
    def test_vault_database_connection_configure_authentication_error(
        self, authenticator, exc, capfd
    ):
        authenticator.authenticate.side_effect = exc

        with pytest.raises(SystemExit) as e:
            vault_database_connection_configure.main()

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
    def test_vault_database_connection_configure_auth_validation_error(
        self, authenticator, exc, capfd
    ):
        authenticator.validate.side_effect = exc

        with pytest.raises(SystemExit) as e:
            vault_database_connection_configure.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)
        assert result["msg"] == "throwaway msg"

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
                r"^Invalid or missing path \['([^']+)/config/([^']+)'\]",
            ),
        ],
    )
    @pytest.mark.parametrize(
        "patch_ansible_module",
        [[_combined_options(), "engine_mount_point"]],
        indirect=True,
    )
    @pytest.mark.parametrize("opt_engine_mount_point", ["path/1", "second/path"])
    def test_vault_database_connection_configure_vault_exception(
        self, vault_client, exc, opt_engine_mount_point, capfd
    ):

        client = vault_client
        client.secrets.database.configure.side_effect = exc[0](exc[1])

        with pytest.raises(SystemExit) as e:
            vault_database_connection_configure.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code != 0, "result: %r" % (result,)
        match = re.search(exc[2], result["msg"])
        assert match is not None, "result: %r\ndid not match: %s" % (result, exc[2])

        assert opt_engine_mount_point == match.group(1)

    @pytest.mark.parametrize(
        "patch_ansible_module", [_combined_options()], indirect=True
    )
    def test_vault_database_connection_configure_success(
        self, patch_ansible_module, empty_response, vault_client, capfd
    ):
        client = vault_client
        client.secrets.database.configure.return_value = empty_response

        with pytest.raises(SystemExit) as e:
            vault_database_connection_configure.main()

        out, err = capfd.readouterr()
        result = json.loads(out)

        assert e.value.code == 0, "result: %r" % (result,)

        client.secrets.database.configure.assert_called_once_with(
            mount_point=patch_ansible_module["engine_mount_point"],
            name=patch_ansible_module["connection_name"],
            plugin_name=patch_ansible_module["plugin_name"],
            allowed_roles=patch_ansible_module["allowed_roles"],
            connection_url=patch_ansible_module["connection_url"],
            username=patch_ansible_module["connection_username"],
            password=patch_ansible_module["connection_password"],
        )

        assert result["changed"] is True
