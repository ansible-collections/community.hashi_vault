# -*- coding: utf-8 -*-
# Copyright (c) 2022 Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible.plugins.lookup import LookupBase
from ansible.errors import AnsibleError

from ...compat import mock

from .....plugins.lookup import vault_ansible_settings

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


# # if True, simulate 2.9 behavior on newer versions
# @pytest.fixture(params=[False, True])
@pytest.fixture
def lookup_loader():
    from ansible.plugins.loader import lookup_loader
    loader = mock.Mock(wraps=lookup_loader)
    return loader


@pytest.fixture
def patch_lookup_loader(lookup_loader):
    with mock.patch('ansible.plugins.loader.lookup_loader', lookup_loader):
        yield lookup_loader


@pytest.fixture
def vault_ansible_settings_lookup(lookup_loader):
    return lookup_loader.get('community.hashi_vault.vault_ansible_settings')


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
        patch_config_manager, sample_options
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

    # @pytest.mark.parametrize('exc', [HashiVaultValueError('dummy msg'), NotImplementedError('dummy msg')])
    # def test_vault_ansible_settings_authentication_error(self, vault_ansible_settings_lookup, minimal_vars, authenticator, exc):
    #     authenticator.authenticate.side_effect = exc

    #     with pytest.raises(AnsibleError, match=r'dummy msg'):
    #         vault_ansible_settings_lookup.run(terms='fake', variables=minimal_vars)

    # @pytest.mark.parametrize('exc', [HashiVaultValueError('dummy msg'), NotImplementedError('dummy msg')])
    # def test_vault_ansible_settings_auth_validation_error(self, vault_ansible_settings_lookup, minimal_vars, authenticator, exc):
    #     authenticator.validate.side_effect = exc

    #     with pytest.raises(AnsibleError, match=r'dummy msg'):
    #         vault_ansible_settings_lookup.run(terms='fake', variables=minimal_vars)

    # @pytest.mark.parametrize('paths', [['fake1'], ['fake2', 'fake3']])
    # @pytest.mark.parametrize('engine_mount_point', ['kv', 'other'])
    # def test_vault_ansible_settings_return_data(self, vault_ansible_settings_lookup, minimal_vars, kv1_get_response, vault_client, paths, engine_mount_point):
    #     client = vault_client

    #     expected_calls = [mock.call(path=p, mount_point=engine_mount_point) for p in paths]

    #     expected = {}
    #     expected['raw'] = kv1_get_response.copy()
    #     expected['metadata'] = kv1_get_response.copy()
    #     expected['data'] = expected['metadata'].pop('data')
    #     expected['secret'] = expected['data']

    #     def _fake_kv1_get(path, mount_point):
    #         r = kv1_get_response.copy()
    #         r['data'] = r['data'].copy()
    #         r['data'].update({'_path': path})
    #         r['data'].update({'_mount': mount_point})
    #         return r

    #     client.secrets.kv.v1.read_secret = mock.Mock(wraps=_fake_kv1_get)

    #     response = vault_ansible_settings_lookup.run(terms=paths, variables=minimal_vars, engine_mount_point=engine_mount_point)

    #     client.secrets.kv.v1.read_secret.assert_has_calls(expected_calls)

    #     assert len(response) == len(paths), "%i paths processed but got %i responses" % (len(paths), len(response))

    #     for p in paths:
    #         r = response.pop(0)
    #         ins_p = r['secret'].pop('_path')
    #         ins_m = r['secret'].pop('_mount')
    #         assert p == ins_p, "expected '_path=%s' field was not found in response, got %r" % (p, ins_p)
    #         assert engine_mount_point == ins_m, "expected '_mount=%s' field was not found in response, got %r" % (engine_mount_point, ins_m)
    #         assert r['raw'] == expected['raw'], (
    #             "remaining response did not match expected\nresponse: %r\nexpected: %r" % (r, expected['raw'])
    #         )
    #         assert r['metadata'] == expected['metadata']
    #         assert r['data'] == expected['data']
    #         assert r['secret'] == expected['secret']

    # @pytest.mark.parametrize(
    #     'exc',
    #     [
    #         (hvac.exceptions.Forbidden, "", r"^Forbidden: Permission Denied to path \['([^']+)'\]"),
    #         (
    #             hvac.exceptions.InvalidPath,
    #             "Invalid path for a versioned K/V secrets engine",
    #             r"^Invalid path for a versioned K/V secrets engine \['[^']+'\]. If this is a KV version 2 path, use community.hashi_vault.vault_kv2_get"
    #         ),
    #         (hvac.exceptions.InvalidPath, "", r"^Invalid or missing path \['[^']+'\]"),
    #     ]
    # )
    # @pytest.mark.parametrize('path', ['path/1', 'second/path'])
    # def test_vault_ansible_settings_exceptions(self, vault_ansible_settings_lookup, minimal_vars, vault_client, path, exc):
    #     client = vault_client

    #     client.secrets.kv.v1.read_secret.side_effect = exc[0](exc[1])

    #     with pytest.raises(AnsibleError) as e:
    #         vault_ansible_settings_lookup.run(terms=[path], variables=minimal_vars)

    #     match = re.search(exc[2], str(e.value))

    #     assert match is not None, "result: %r\ndid not match: %s" % (e.value, exc[2])

    #     try:
    #         assert path == match.group(1), "expected: %s\ngot: %s" % (match.group(1), path)
    #     except IndexError:
    #         pass
