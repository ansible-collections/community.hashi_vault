#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2024, Aaron Schif
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
  module: vault_approle_files
  version_added: "7.3.0"
  author:
    - Aaron Schif (@aaronschif)
  short_description: Ensure AppRole credentials are written to files on the managed host
  requirements:
    - C(hvac) (L(Python library,https://hvac.readthedocs.io/en/stable/overview.html)) on the B(control node), not the managed host.
    - For detailed requirements, see R(the collection requirements page,ansible_collections.community.hashi_vault.docsite.user_guide.requirements).
  description:
    - Writes AppRole credentials (C(role_id), C(secret_id), and C(secret_id_accessor)) to files on the managed host.
    - All Vault API calls are made from the B(control node). The managed host does not need network access to Vault
      and does not need the C(hvac) library installed.
    - If the files already exist, verifies that the C(secret_id) is still active for the specified role before deciding
      whether to generate new credentials.
    - Optionally validates the role's configuration parameters in Vault against expected values before any credential operation.
    - This module does not configure the AppRole role; it only obtains a C(secret_id).
  notes:
    - The C(secret_id) is written to I(secret_id_file) but is never included in module output.
      Use C(no_log: true) on this task to prevent the C(secret_id) from appearing in verbose Ansible output.
    - Files are written with permissions set by I(mode). The parent directories must already exist on the managed host.
    - When I(role_params) is specified, the parameters are compared against what Vault returns from C(read_role).
      List-valued parameters are compared without regard to order.
  attributes:
    check_mode:
      support: partial
      details:
        - In check mode, no files are written and no C(secret_id) is generated.
        - If existing credential files are found and the C(secret_id) is still valid, C(changed=False) is returned.
        - Otherwise C(changed=True) is reported but no credentials are generated or written.
  seealso:
    - module: community.hashi_vault.vault_write
    - module: community.hashi_vault.vault_read
  extends_documentation_fragment:
    - community.hashi_vault.attributes
    - community.hashi_vault.attributes.action_group
    - community.hashi_vault.connection
    - community.hashi_vault.auth
  options:
    role_name:
      description: Name of the AppRole role.
      type: str
      required: true
    mount_point:
      description: Mount point for the AppRole auth method.
      type: str
      default: approle
    secret_id_file:
      description: Path on the managed host where the C(secret_id) will be written.
      type: path
      required: true
    role_id_file:
      description: Path on the managed host where the C(role_id) will be written.
      type: path
      required: true
    secret_id_accessor_file:
      description:
        - Path on the managed host where the C(secret_id_accessor) will be written.
        - Defaults to I(secret_id_file) with C(_accessor) appended.
      type: path
      default: null
    role_params:
      description:
        - A dictionary of expected role configuration parameters.
        - Each key is compared against the corresponding field returned by Vault's C(read_role) API.
        - The module fails if any specified parameter does not match the role's actual configuration.
        - Useful as a pre-flight safety check (e.g. verifying the correct policies or TTL) before obtaining credentials.
        - Common parameters include C(token_policies), C(token_ttl), C(secret_id_ttl), C(secret_id_num_uses), and C(bind_secret_id).
      type: dict
      default: null
    mode:
      description:
        - Permission mode for the credential files, as an octal string (e.g. C('0600')).
        - Applied to all three files.
      type: raw
      default: '0600'
    owner:
      description:
        - Name of the user that should own the credential files.
        - Requires the Ansible connection user to have C(chown) rights (typically root).
        - When omitted the files are owned by whichever user Ansible connects as.
      type: str
      default: null
    group:
      description:
        - Name of the group that should own the credential files.
        - When omitted the group is determined by the remote OS defaults.
      type: str
      default: null
    force:
      description:
        - When C(true), generate a new C(secret_id) even if the existing files are present and the C(secret_id) is still valid.
      type: bool
      default: false
"""

EXAMPLES = """
- name: Ensure AppRole credential files are present and valid
  community.hashi_vault.vault_approle_files:
    url: https://vault:8201
    auth_method: token
    token: "{{ vault_token }}"
    role_name: my-role
    secret_id_file: /etc/myapp/vault_secret_id
    role_id_file: /etc/myapp/vault_role_id


- name: Validate role configuration before obtaining credentials
  community.hashi_vault.vault_approle_files:
    url: https://vault:8201
    auth_method: token
    token: "{{ vault_token }}"
    role_name: my-role
    secret_id_file: /etc/myapp/vault_secret_id
    role_id_file: /etc/myapp/vault_role_id

    role_params:
      token_policies:
        - my-policy
        - default
      secret_id_num_uses: 0
      bind_secret_id: true

- name: Force credential rotation
  community.hashi_vault.vault_approle_files:
    url: https://vault:8201
    auth_method: token
    token: "{{ vault_token }}"
    role_name: my-role
    secret_id_file: /etc/myapp/vault_secret_id
    role_id_file: /etc/myapp/vault_role_id

    force: true
"""

RETURN = """
role_id:
  description: The C(role_id) associated with the AppRole. C(null) in check mode when credentials would be generated.
  returned: success
  type: str
secret_id_accessor:
  description:
    - The accessor for the C(secret_id). Can be used to look up or revoke the C(secret_id) without exposing its value.
    - C(null) in check mode when credentials would be generated.
  returned: success
  type: str
"""

# This module is backed entirely by the vault_approle_files action plugin.
# All logic — including Vault API calls — runs on the control node.
# This file exists solely so that ansible-doc can read the documentation above.
