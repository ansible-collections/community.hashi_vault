===================================
community.hashi_vault Release Notes
===================================

.. contents:: Topics


v1.0.0
======

Release Summary
---------------

Our first major release contains a single breaking change that will affect only a small subset of users. No functionality is removed. See the details in the changelog to determine if you're affected and if so how to transition to remediate.

Breaking Changes / Porting Guide
--------------------------------

- hashi_vault - the ``VAULT_ADDR`` environment variable is now checked last for the ``url`` parameter. For details on which use cases are impacted, see (https://github.com/ansible-collections/community.hashi_vault/issues/8).

v0.2.0
======

Release Summary
---------------

Several backwards-compatible bugfixes and enhancements in this release.
Some environment variables are deprecated and have standardized replacements.

Minor Changes
-------------

- Add optional ``aws_iam_server_id`` parameter as the value for ``X-Vault-AWS-IAM-Server-ID`` header (https://github.com/ansible-collections/community.hashi_vault/pull/27).
- hashi_vault - ``ANSIBLE_HASHI_VAULT_ADDR`` environment variable added for option ``url`` (https://github.com/ansible-collections/community.hashi_vault/issues/8).
- hashi_vault - ``ANSIBLE_HASHI_VAULT_AUTH_METHOD`` environment variable added for option ``auth_method`` (https://github.com/ansible-collections/community.hashi_vault/issues/17).
- hashi_vault - ``ANSIBLE_HASHI_VAULT_ROLE_ID`` environment variable added for option ``role_id`` (https://github.com/ansible-collections/community.hashi_vault/issues/20).
- hashi_vault - ``ANSIBLE_HASHI_VAULT_SECRET_ID`` environment variable added for option ``secret_id`` (https://github.com/ansible-collections/community.hashi_vault/issues/20).
- hashi_vault - ``ANSIBLE_HASHI_VAULT_TOKEN_FILE`` environment variable added for option ``token_file`` (https://github.com/ansible-collections/community.hashi_vault/issues/15).
- hashi_vault - ``ANSIBLE_HASHI_VAULT_TOKEN_PATH`` environment variable added for option ``token_path`` (https://github.com/ansible-collections/community.hashi_vault/issues/15).
- hashi_vault - ``namespace`` parameter can be specified in INI or via env vars ``ANSIBLE_HASHI_VAULT_NAMESPACE`` (new) and ``VAULT_NAMESPACE`` (lower preference)  (https://github.com/ansible-collections/community.hashi_vault/issues/14).
- hashi_vault - ``token`` parameter can now be specified via ``ANSIBLE_HASHI_VAULT_TOKEN`` as well as via ``VAULT_TOKEN`` (the latter with lower preference) (https://github.com/ansible-collections/community.hashi_vault/issues/16).
- hashi_vault - add ``token_validate`` option to control token validation (https://github.com/ansible-collections/community.hashi_vault/pull/24).
- hashi_vault - uses new AppRole method in hvac 0.10.6 with fallback to deprecated method with warning (https://github.com/ansible-collections/community.hashi_vault/pull/33).

Deprecated Features
-------------------

- hashi_vault - ``VAULT_ADDR`` environment variable for option ``url`` will have its precedence lowered in 1.0.0; use ``ANSIBLE_HASHI_VAULT_ADDR`` to intentionally override a config value (https://github.com/ansible-collections/community.hashi_vault/issues/8).
- hashi_vault - ``VAULT_AUTH_METHOD`` environment variable for option ``auth_method`` will be removed in 2.0.0, use ``ANSIBLE_HASHI_VAULT_AUTH_METHOD`` instead (https://github.com/ansible-collections/community.hashi_vault/issues/17).
- hashi_vault - ``VAULT_ROLE_ID`` environment variable for option ``role_id`` will be removed in 2.0.0, use ``ANSIBLE_HASHI_VAULT_ROLE_ID`` instead (https://github.com/ansible-collections/community.hashi_vault/issues/20).
- hashi_vault - ``VAULT_SECRET_ID`` environment variable for option ``secret_id`` will be removed in 2.0.0, use ``ANSIBLE_HASHI_VAULT_SECRET_ID`` instead (https://github.com/ansible-collections/community.hashi_vault/issues/20).
- hashi_vault - ``VAULT_TOKEN_FILE`` environment variable for option ``token_file`` will be removed in 2.0.0, use ``ANSIBLE_HASHI_VAULT_TOKEN_FILE`` instead (https://github.com/ansible-collections/community.hashi_vault/issues/15).
- hashi_vault - ``VAULT_TOKEN_PATH`` environment variable for option ``token_path`` will be removed in 2.0.0, use ``ANSIBLE_HASHI_VAULT_TOKEN_PATH`` instead (https://github.com/ansible-collections/community.hashi_vault/issues/15).

Bugfixes
--------

- hashi_vault - ``mount_point`` parameter did not work with ``aws_iam_login`` auth method (https://github.com/ansible-collections/community.hashi_vault/issues/7)
- hashi_vault - fallback logic for handling deprecated style of auth in hvac was not implemented correctly (https://github.com/ansible-collections/community.hashi_vault/pull/33).
- hashi_vault - parameter ``mount_point`` does not work with JWT auth (https://github.com/ansible-collections/community.hashi_vault/issues/29).
- hashi_vault - tokens without ``lookup-self`` ability can't be used because of validation (https://github.com/ansible-collections/community.hashi_vault/issues/18).

v0.1.0
======

Release Summary
---------------

Our first release matches the ``hashi_vault`` lookup functionality provided by ``community.general`` version ``1.3.0``.

