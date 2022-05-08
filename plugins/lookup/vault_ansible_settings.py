# (c) 2022, Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
name: vault_ansible_settings
version_added: 2.5.0
author:
  - Brian Scholer (@briantist)
short_description: Returns
description:
  - Performs a generic write operation against a given path in HashiCorp Vault, returning any output.
seealso:
  - ref: community.hashi_vault Lookup Guide <ansible_collections.community.hashi_vault.docsite.lookup_guide>
    description: Guidance on using lookups in C(community.hashi_vault).
notes:
  - This collection supports some "low precedence" environment variables that get loaded after all other sources, such as C(VAULT_ADDR).
  - These environment variables B(are not supported) with this plugin.
  - If you wish to use them, use the R(ansible.builtin.env lookup,ansible_collections.ansible.builtin.env_lookup) to
    load them directly when calling a module or setting C(module_defaults).
  - Similarly, any options that rely on additional processing to fill in their values will not have that done.
  - For example, tokens will not be loaded from the token sink file, auth methods will not have their C(validate()) methods called.
  - See the R(Lookup Guide,ansible_collections.community.hashi_vault.docsite.lookup_guide) for more information.
options:
  _terms:
    description:
      - The names of the options to load.
      - Supports C(fnmatch) L(style wildcards,https://docs.python.org/3/library/fnmatch.html).
      - Prepend any name or pattern with C(!) to invert the match.
    type: list
    elements: str
    required: false
    default: ['*']
  plugin:
    description:
      - The name of the plugin whose options will be returned.
      - Only lookups are supported.
      - Short names (without a dot C(.)) will be fully qualified with C(community.hashi_vault).
    type: str
    default: community.hashi_vault.vault_login
  include_private:
    description: Include options that begin with underscore C(_).
    type: bool
    default: false
  include_none:
    description: Include options whose value is C(None) (this usually means they are unset).
    type: bool
    default: false
  include_default:
    description: Include options whose value comes from a default.
    type: bool
    default: false
'''

EXAMPLES = """
# These examples show some uses that might work well as a lookup.
# For most uses, the vault_write module should be used.

- name: Retrieve and display random data
  vars:
    data:
      format: hex
    num_bytes: 64
  ansible.builtin.debug:
    msg: "{{ lookup('community.hashi_vault.vault_write', 'sys/tools/random/' ~ num_bytes, data=data) }}"

- name: Hash some data and display the hash
  vars:
    input: |
      Lorem ipsum dolor sit amet, consectetur adipiscing elit.
      Pellentesque posuere dui a ipsum dapibus, et placerat nibh bibendum.
    data:
      input: '{{ input | b64encode }}'
    hash_algo: sha2-256
  ansible.builtin.debug:
    msg: "The hash is {{ lookup('community.hashi_vault.vault_write', 'sys/tools/hash/' ~ hash_algo, data=data) }}"


# In this next example, the Ansible controller's token does not have permission to read the secrets we need.
# It does have permission to generate new secret IDs for an approle which has permission to read the secrets,
# however the approle is configured to:
# 1) allow a maximum of 1 use per secret ID
# 2) restrict the IPs allowed to use login using the approle to those of the remote hosts
#
# Normally, the fact that a new secret ID would be generated on every loop iteration would not be desirable,
# but here it's quite convenient.

- name: Retrieve secrets from the remote host with one-time-use approle creds
  vars:
    role_id: "{{ lookup('community.hashi_vault.vault_read', 'auth/approle/role/role-name/role-id') }}"
    secret_id: "{{ lookup('community.hashi_vault.vault_write', 'auth/approle/role/role-name/secret-id') }}"
  community.hashi_vault.vault_read:
    auth_method: approle
    role_id: '{{ role_id }}'
    secret_id: '{{ secret_id }}'
    path: '{{ item }}'
  register: secret_data
  loop:
    - secret/data/secret1
    - secret/data/app/deploy-key
    - secret/data/access-codes/self-destruct


# This time we have a secret values on the controller, and we need to run a command the remote host,
# that is expecting to a use single-use token as input, so we need to use wrapping to send the data.

- name: Run a command that needs wrapped secrets
  vars:
    secrets:
      secret1: '{{ my_secret_1 }}'
      secret2: '{{ second_secret }}'
    wrapped: "{{ lookup('community.hashi_vault.vault_write', 'sys/wrapping/wrap', data=secrets) }}"
  ansible.builtin.command: 'vault unwrap {{ wrapped }}'
"""

RETURN = r'''
_raw:
  description:
    - A dictionary of the options and their values.
    - Only a single dictionary will be returned, even with multiple terms.
  type: dict
'''

from fnmatch import fnmatchcase

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible import constants as C
from ansible.plugins.loader import lookup_loader
from ansible.utils.display import Display


display = Display()


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        self.set_options(direct=kwargs, var_options=variables)

        include_private = self.get_option('include_private')
        include_none = self.get_option('include_none')
        include_default = self.get_option('include_default')

        plugin = self.get_option('plugin')
        if '.' not in plugin:
            plugin = 'community.hashi_vault.' + plugin

        if not terms:
            terms = ['*']

        opts = {}

        try:
            # ansible-core 2.10 or later
            p = lookup_loader.find_plugin_with_context(plugin)
            loadname = p.plugin_resolved_name
            resolved = p.resolved
        except AttributeError:
            # ansible 2.9
            p = lookup_loader.find_plugin_with_name(plugin)
            loadname = p[0]
            resolved = loadname is not None

        if not resolved:
            raise AnsibleError("'%s' plugin not found." % plugin)

        # Loading ensures that the options are initialized in ConfigManager
        lookup_loader.get(plugin, class_only=True)

        pluginget = C.config.get_configuration_definitions('lookup', loadname)

        for option in pluginget.keys():
            if not include_private and option.startswith('_'):
                continue

            keep = False
            for pattern in terms:
                if pattern.startswith('!'):
                    if keep and fnmatchcase(option, pattern[1:]):
                        keep = False
                else:
                    keep = keep or fnmatchcase(option, pattern)

            if not keep:
                continue

            value, origin = C.config.get_config_value_and_origin(option, None, 'lookup', loadname, None, variables=variables)
            if (include_none or value is not None) and (include_default or origin != 'default'):
                opts[option] = value

        return [opts]
