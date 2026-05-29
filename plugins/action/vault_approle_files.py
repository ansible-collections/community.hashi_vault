# -*- coding: utf-8 -*-
# (c) 2024, Aaron Schif
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import base64
import os
import tempfile

from ansible.errors import AnsibleActionFail
from ansible.plugins.action import ActionBase
from ansible.utils.display import Display
from ansible.module_utils.common.text.converters import to_text

display = Display()


def _params_match(expected, actual):
    if isinstance(expected, list) and isinstance(actual, list):
        return sorted(to_text(x) for x in expected) == sorted(to_text(x) for x in actual)
    return expected == actual


class ActionModule(ActionBase):
    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):
        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp

        if task_vars is None:
            task_vars = dict()

        # These imports happen on the controller, so hvac must be present there.
        try:
            from ansible_collections.community.hashi_vault.plugins.module_utils._hashi_vault_common import (
                HashiVaultHelper,
                HashiVaultHVACError,
                HashiVaultOptionAdapter,
                HashiVaultValueError,
            )
            from ansible_collections.community.hashi_vault.plugins.module_utils._connection_options import HashiVaultConnectionOptions
            from ansible_collections.community.hashi_vault.plugins.module_utils._authenticator import HashiVaultAuthenticator
        except ImportError as e:
            raise AnsibleActionFail("Failed to import hashi_vault module utils: %s" % to_text(e))

        args = self._task.args

        # Module-specific parameters
        role_name = args.get('role_name')
        if not role_name:
            raise AnsibleActionFail("role_name is required")

        secret_id_file = args.get('secret_id_file')
        if not secret_id_file:
            raise AnsibleActionFail("secret_id_file is required")

        role_id_file = args.get('role_id_file')
        if not role_id_file:
            raise AnsibleActionFail("role_id_file is required")

        # mount_point serves as both the AppRole management mount and the auth mount_point;
        # it defaults to 'approle', matching what generate_argspec would produce.
        mount_point = args.get('mount_point', 'approle')
        accessor_file = args.get('secret_id_accessor_file') or (secret_id_file + '_accessor')
        role_params = args.get('role_params')
        mode = args.get('mode', '0600')
        owner = args.get('owner')
        group = args.get('group')
        force = args.get('force', False)

        # Build the params dict for Vault connection/auth utilities from their ARGSPECs,
        # overriding defaults with any values the user provided in the task.
        params = {}
        for key, spec in HashiVaultConnectionOptions.ARGSPEC.items():
            params[key] = args.get(key, spec.get('default'))
        for key, spec in HashiVaultAuthenticator.ARGSPEC.items():
            params[key] = args.get(key, spec.get('default'))
        params['mount_point'] = mount_point

        # Initialise Vault utilities — all Vault API calls happen on the controller.
        try:
            helper = HashiVaultHelper()
        except HashiVaultHVACError as exc:
            raise AnsibleActionFail(exc.msg)

        hvac_exceptions = helper.get_hvac().exceptions

        def _retry_callback_generator(retry_action):
            def _on_retry(retry_obj):
                if retry_obj.total > 0 and retry_action == 'warn':
                    display.warning(
                        'community.hashi_vault: %i %s remaining.' % (
                            retry_obj.total, 'retry' if retry_obj.total == 1 else 'retries',
                        )
                    )
            return _on_retry

        adapter = HashiVaultOptionAdapter.from_dict(params)
        connection_options = HashiVaultConnectionOptions(
            option_adapter=adapter,
            retry_callback_generator=_retry_callback_generator,
        )
        authenticator = HashiVaultAuthenticator(
            option_adapter=adapter,
            warning_callback=display.warning,
            deprecate_callback=display.deprecated,
        )

        try:
            connection_options.process_connection_options()
            client_args = connection_options.get_hvac_connection_options()
            client = helper.get_vault_client(**client_args)
            authenticator.validate()
            authenticator.authenticate(client)
        except (NotImplementedError, HashiVaultValueError) as e:
            raise AnsibleActionFail(to_text(e))
        except Exception as e:
            raise AnsibleActionFail("Vault connection failed: %s" % to_text(e))

        # Optional: validate role configuration before touching credentials.
        if role_params is not None:
            try:
                role_data = client.auth.approle.read_role(role_name=role_name, mount_point=mount_point)
            except hvac_exceptions.Forbidden:
                raise AnsibleActionFail(
                    "Forbidden: Cannot read role '%s' at mount '%s' for parameter validation." % (role_name, mount_point)
                )
            except hvac_exceptions.InvalidPath:
                raise AnsibleActionFail("Role '%s' not found at mount '%s'." % (role_name, mount_point))

            actual_role = role_data.get('data', {})
            mismatches = [
                "'%s': expected %r, got %r" % (key, expected_val, actual_role.get(key))
                for key, expected_val in role_params.items()
                if not _params_match(expected_val, actual_role.get(key))
            ]
            if mismatches:
                raise AnsibleActionFail("Role parameter mismatch for '%s': %s" % (role_name, '; '.join(mismatches)))

        # Check whether all credential files exist on the target host.
        def _stat_exists(path):
            r = self._execute_module(module_name='stat', module_args={'path': path}, task_vars=task_vars)
            if r.get('failed'):
                raise AnsibleActionFail("Failed to stat '%s': %s" % (path, r.get('msg', '')))
            return r.get('stat', {}).get('exists', False)

        def _slurp(path):
            r = self._execute_module(module_name='slurp', module_args={'src': path}, task_vars=task_vars)
            if r.get('failed'):
                raise AnsibleActionFail("Failed to read '%s' from target: %s" % (path, r.get('msg', '')))
            return base64.b64decode(r['content']).decode('utf-8').strip()

        def _enforce_file_attrs(paths):
            """Apply mode/owner/group to existing files; returns True if anything changed."""
            base_args = dict(state='file', mode=mode)
            if owner is not None:
                base_args['owner'] = owner
            if group is not None:
                base_args['group'] = group
            changed = False
            for path in paths:
                r = self._execute_module(
                    module_name='file',
                    module_args=dict(base_args, path=path),
                    task_vars=task_vars,
                )
                if r.get('failed'):
                    raise AnsibleActionFail("Failed to set attributes on '%s': %s" % (path, r.get('msg', '')))
                if r.get('changed'):
                    changed = True
            return changed

        all_files_exist = all(_stat_exists(p) for p in [secret_id_file, role_id_file, accessor_file])

        if all_files_exist and not force:
            existing_secret_id = _slurp(secret_id_file)

            lookup_fn = (
                getattr(client.auth.approle, 'read_secret_id', None)
                or getattr(client.auth.approle, 'lookup_secret_id', None)
            )
            if lookup_fn is None:
                raise AnsibleActionFail(
                    "hvac AppRole API has no secret_id lookup method; upgrade hvac."
                )
            try:
                lookup_fn(
                    role_name=role_name,
                    secret_id=existing_secret_id,
                    mount_point=mount_point,
                )
                existing_role_id = _slurp(role_id_file)
                existing_accessor = _slurp(accessor_file)
                attrs_changed = _enforce_file_attrs([secret_id_file, role_id_file, accessor_file])
                result['changed'] = attrs_changed
                result['role_id'] = existing_role_id
                result['secret_id_accessor'] = existing_accessor
                return result
            except (hvac_exceptions.InvalidPath, hvac_exceptions.InvalidRequest):
                pass  # secret_id is expired or invalid — regenerate
            except hvac_exceptions.Forbidden:
                raise AnsibleActionFail(
                    "Forbidden: Cannot look up secret_id for role '%s'. "
                    "Ensure the Vault token has permission on the lookup-secret-id endpoint." % role_name
                )

        # New credentials are required.
        if self._play_context.check_mode:
            result['changed'] = True
            result['role_id'] = None
            result['secret_id_accessor'] = None
            return result

        try:
            role_id_response = client.auth.approle.read_role_id(role_name=role_name, mount_point=mount_point)
            role_id = (role_id_response or {}).get('data', {}).get('role_id')
            if not role_id:
                raise AnsibleActionFail("Vault returned no role_id for role '%s'." % role_name)
        except hvac_exceptions.Forbidden:
            raise AnsibleActionFail("Forbidden: Cannot read role_id for role '%s'." % role_name)
        except hvac_exceptions.InvalidPath:
            raise AnsibleActionFail("Role '%s' not found at mount '%s'." % (role_name, mount_point))

        try:
            secret_id_response = client.auth.approle.generate_secret_id(role_name=role_name, mount_point=mount_point)
            data = (secret_id_response or {}).get('data', {})
            secret_id = data.get('secret_id')
            secret_id_accessor = data.get('secret_id_accessor')
            if not secret_id:
                raise AnsibleActionFail("Vault returned no secret_id for role '%s'." % role_name)
        except hvac_exceptions.Forbidden:
            raise AnsibleActionFail("Forbidden: Cannot generate secret_id for role '%s'." % role_name)
        except hvac_exceptions.InvalidPath:
            raise AnsibleActionFail("Role '%s' not found at mount '%s'." % (role_name, mount_point))

        # Write the three credential files to the target host.
        #
        # _execute_module('copy', content=...) runs the copy MODULE directly on the remote,
        # bypassing the copy ACTION PLUGIN that normally converts 'content' into a temp file
        # and sets 'src'. The module alone doesn't handle 'content', so we must:
        #   1. write content to a local temp file (mode 0600, so it is never world-readable)
        #   2. transfer it to a remote temp dir via Ansible's connection
        #   3. use copy with remote_src=True to move it to the final destination
        #
        # Set no_log: true on this task to prevent the secret_id from appearing in verbose logs.
        remote_tmp_dir = self._make_tmp_path()

        for path, content in [
            (role_id_file, role_id),
            (secret_id_file, secret_id),
            (accessor_file, secret_id_accessor),
        ]:
            local_tmp = None
            try:
                fd, local_tmp = tempfile.mkstemp()
                try:
                    os.write(fd, content.encode('utf-8'))
                finally:
                    os.close(fd)

                remote_tmp = self._connection._shell.join_path(remote_tmp_dir, os.path.basename(local_tmp))
                try:
                    self._transfer_file(local_tmp, remote_tmp)
                except Exception as e:
                    raise AnsibleActionFail("Failed to transfer credential to target: %s" % to_text(e))
            finally:
                if local_tmp:
                    try:
                        os.unlink(local_tmp)
                    except OSError:
                        pass

            copy_args = dict(src=remote_tmp, dest=path, mode=mode, remote_src=True)
            if owner is not None:
                copy_args['owner'] = owner
            if group is not None:
                copy_args['group'] = group

            copy_result = self._execute_module(
                module_name='copy',
                module_args=copy_args,
                task_vars=task_vars,
            )
            if copy_result.get('failed'):
                result['failed'] = True
                result['msg'] = "Failed to write '%s' to target: %s" % (path, copy_result.get('msg', ''))
                return result

        result['changed'] = True
        result['role_id'] = role_id
        result['secret_id_accessor'] = secret_id_accessor
        return result
