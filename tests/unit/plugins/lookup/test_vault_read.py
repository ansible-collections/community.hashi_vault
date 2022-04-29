# -*- coding: utf-8 -*-
# Copyright (c) 2022 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible.plugins.loader import lookup_loader
from ansible.errors import AnsibleError

from ...compat import mock

from .....plugins.plugin_utils._hashi_vault_lookup_base import HashiVaultLookupBase
from .....plugins.module_utils._hashi_vault_common import HashiVaultValueError

from .....plugins.lookup import vault_read


hvac = pytest.importorskip('hvac')


pytestmark = pytest.mark.usefixtures(
    'patch_authenticator',
    'patch_get_vault_client',
)


@pytest.fixture
def vault_read_lookup():
    return lookup_loader.get('community.hashi_vault.vault_read')


class TestVaultReadLookup(object):

    def test_vault_read_is_lookup_base(self, vault_read_lookup):
        assert issubclass(type(vault_read_lookup), HashiVaultLookupBase)

    def test_vault_read_no_hvac(self, vault_read_lookup, minimal_vars):
        with mock.patch.object(vault_read, 'HVAC_IMPORT_ERROR', new=ImportError()):
            with pytest.raises(AnsibleError, match=r"This plugin requires the 'hvac' Python library"):
                vault_read_lookup.run(terms='fake', variables=minimal_vars)

    @pytest.mark.parametrize('exc', [HashiVaultValueError('dummy msg'), NotImplementedError('dummy msg')])
    def test_vault_read_authentication_error(self, vault_read_lookup, minimal_vars, authenticator, exc):
        authenticator.authenticate.side_effect = exc

        with pytest.raises(AnsibleError, match=r'dummy msg'):
            vault_read_lookup.run(terms='fake', variables=minimal_vars)

    @pytest.mark.parametrize('exc', [HashiVaultValueError('dummy msg'), NotImplementedError('dummy msg')])
    def test_vault_read_auth_validation_error(self, vault_read_lookup, minimal_vars, authenticator, exc):
        authenticator.validate.side_effect = exc

        with pytest.raises(AnsibleError, match=r'dummy msg'):
            vault_read_lookup.run(terms='fake', variables=minimal_vars)
