# -*- coding: utf-8 -*-
# Copyright (c) 2022 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import re

from ansible.plugins.lookup import LookupBase
from ansible.errors import AnsibleError

from ...compat import mock


OPTIONS = {
    '_terms': (None, 'default'),
    '_private1': (1, 'default'),
    '_private2': (2, 'env'),
    '_private3': (None, 'variable'),
    'optionA': ('A', 'env'),
    'optionB': ('B', 'default'),
    'optionC': ('C', '/tmp/ansible.cfg'),
    'Doption': ('D', 'variable'),
}


@pytest.fixture
def sample_options():
    return OPTIONS.copy()


@pytest.fixture
def patch_config_manager(sample_options):
    def _config_value_and_origin(name, *args, **kwargs):
        return sample_options[name]

    from ansible.constants import config as C
    config = mock.Mock(wraps=C)
    config.get_configuration_definitions.return_value = sample_options.copy()
    config.get_config_value_and_origin = mock.Mock(wraps=_config_value_and_origin)

    with mock.patch('ansible.constants.config', config):
        yield config


@pytest.fixture
def vault_ansible_settings_lookup(loader):
    return loader.get('community.hashi_vault.vault_ansible_settings')


@pytest.fixture(params=[False, True])
def loader(request):
    from ansible.plugins.loader import lookup_loader as orig_loader

    def _legacy_sim(plugin):
        r = orig_loader.find_plugin_with_context(plugin)
        return (r.plugin_resolved_name, None)

    loader = mock.Mock(wraps=orig_loader)

    if request.param:
        loader.find_plugin_with_context.side_effect = AttributeError
        loader.find_plugin_with_name = mock.Mock(wraps=_legacy_sim)

    with mock.patch('ansible.plugins.loader.lookup_loader', loader):
        yield loader


class TestVaultAnsibleSettingsLookup(object):

    def test_vault_ansible_settings_is_lookup_base(self, vault_ansible_settings_lookup):
        assert issubclass(type(vault_ansible_settings_lookup), LookupBase)

    @pytest.mark.parametrize('opt_plugin', ['community.hashi_vault.vault_login', 'vault_login'], ids=['plugin=fqcn', 'plugin=short'])
    @pytest.mark.parametrize('opt_inc_none', [True, False], ids=lambda x: 'none=%s' % x)
    @pytest.mark.parametrize('opt_inc_default', [True, False], ids=lambda x: 'default=%s' % x)
    @pytest.mark.parametrize('opt_inc_private', [True, False], ids=lambda x: 'private=%s' % x)
    @pytest.mark.parametrize('variables', [
        {},
        dict(ansible_hashi_vault_retries=7, ansible_hashi_vault_url='https://the.money.bin'),
    ])
    @pytest.mark.parametrize(['terms', 'expected'], [
        ([], ['_terms', '_private1', '_private2', '_private3', 'optionA', 'optionB', 'optionC', 'Doption']),
        (['*'], ['_terms', '_private1', '_private2', '_private3', 'optionA', 'optionB', 'optionC', 'Doption']),
        (['opt*'], ['optionA', 'optionB', 'optionC']),
        (['*', '!opt*'], ['_terms', '_private1', '_private2', '_private3', 'Doption']),
        (['*', '!*opt*', 'option[B-C]'], ['_terms', '_private1', '_private2', '_private3', 'optionB', 'optionC']),
    ])
    def test_vault_ansible_settings_stuff(
        self, vault_ansible_settings_lookup,
        opt_plugin, opt_inc_none, opt_inc_default, opt_inc_private, variables, terms, expected,
        patch_config_manager, sample_options, loader
    ):
        kwargs = dict(
            plugin=opt_plugin,
            include_default=opt_inc_default,
            include_none=opt_inc_none,
            include_private=opt_inc_private
        )

        result = vault_ansible_settings_lookup.run(terms, variables, **kwargs)

        # this lookup always returns a single dictionary
        assert isinstance(result, list)
        assert len(result) == 1
        deresult = result[0]
        assert isinstance(deresult, dict)

        patch_config_manager.get_configuration_definitions.assert_called_once()

        fqplugin = re.sub(r'^(?:community\.hashi_vault\.)?(.*?)$', r'community.hashi_vault.\1', opt_plugin)
        if hasattr(loader, 'find_plugin_with_name'):
            loader.find_plugin_with_name.assert_called_once_with(fqplugin)
        else:
            loader.find_plugin_with_context.assert_called_once_with(fqplugin)

        # the calls to get_config_value_and_origin vary, get the whole list of calls
        cvocalls = patch_config_manager.get_config_value_and_origin.call_args_list

        for call in cvocalls:
            # 1) ensure variables are always included in this call
            # 2) ensure this method is only called for expected keys (after filtering)
            margs, mkwargs = call
            assert 'variables' in mkwargs and mkwargs['variables'] == variables, call
            assert margs[0] in expected

        # go through all expected keys, ensuring they are in the result,
        # or that they had a reason not to be.
        for ex in expected:
            skip_private = not opt_inc_private and ex.startswith('_')
            skip_none = not opt_inc_none and sample_options[ex][0] is None
            skip_default = not opt_inc_default and sample_options[ex][1] == 'default'
            skip = skip_private or skip_none or skip_default

            assert ex in deresult or skip

            # ensure all expected keys (other than skipped private) had their values checked
            if not skip_private:
                assert any(call[0][0] == ex for call in cvocalls)

        # now check the results:
        # 1) ensure private values are not present when they should not be
        # 2) ensure None values are not present when they should not be
        # 3) ensure values derived from defaults are not present when they should not be
        # 4) ensure the value returned is the correct value
        for k, v in deresult.items():
            assert opt_inc_private or not k.startswith('_')
            assert opt_inc_none or v is not None
            assert opt_inc_default or sample_options[k][1] != 'default'
            assert v == sample_options[k][0]

    def test_vault_ansible_settings_plugin_not_found(self, vault_ansible_settings_lookup):
        with pytest.raises(AnsibleError, match=r"'_ns._col._fake' plugin not found\."):
            vault_ansible_settings_lookup.run([], plugin='_ns._col._fake')
