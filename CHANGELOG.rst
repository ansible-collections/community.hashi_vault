===================================
community.hashi_vault Release Notes
===================================

.. contents:: Topics


v1.3.2
======

Release Summary
---------------

This release adds requirements detection support for Ansible Execution Environments. It also updates and adds new guides in our `collection docsite <https://docs.ansible.com/ansible/devel/collections/community/hashi_vault>`_.
This release also announces the dropping of Python 3.5 support in version ``2.0.0`` of the collection, alongside the previous announcement dropping Python 2.x in ``2.0.0``.

Minor Changes
-------------

- hashi_vault collection - add ``execution-environment.yml`` and a python requirements file to better support ``ansible-builder`` (https://github.com/ansible-collections/community.hashi_vault/pull/105).

Deprecated Features
-------------------

- hashi_vault collection - support for Python 3.5 will be dropped in version ``2.0.0`` of ``community.hashi_vault`` (https://github.com/ansible-collections/community.hashi_vault/issues/81).

v1.3.1
======

Release Summary
---------------

This release fixes an error in the documentation. No functionality is changed so it's not necessary to upgrade from ``1.3.0``.

v1.3.0
======

Release Summary
---------------

This release adds two connection-based options for controlling timeouts and retrying failed Vault requests.

Minor Changes
-------------

- hashi_vault lookup - add ``retries`` and ``retry_action`` to enable built-in retry on failure (https://github.com/ansible-collections/community.hashi_vault/pull/71).
- hashi_vault lookup - add ``timeout`` option to control connection timeouts (https://github.com/ansible-collections/community.hashi_vault/pull/100).

v1.2.0
======

Release Summary
---------------

This release brings several new ways of accessing options, like using Ansible vars, and addng new environment variables and INI config entries.
A special ``none`` auth type is also added, for working with certain Vault Agent configurations.
This release also announces the deprecation of Python 2 support in version ``2.0.0`` of the collection.

Minor Changes
-------------

- hashi_vault lookup - add ``ANSIBLE_HASHI_VAULT_CA_CERT`` env var (with ``VAULT_CACERT`` low-precedence fallback) for ``ca_cert`` option (https://github.com/ansible-collections/community.hashi_vault/pull/97).
- hashi_vault lookup - add ``ANSIBLE_HASHI_VAULT_PASSWORD`` env var and ``ansible_hashi_vault_password`` ansible var for ``password`` option (https://github.com/ansible-collections/community.hashi_vault/pull/96).
- hashi_vault lookup - add ``ANSIBLE_HASHI_VAULT_USERNAME`` env var and ``ansible_hashi_vault_username`` ansible var for ``username`` option (https://github.com/ansible-collections/community.hashi_vault/pull/96).
- hashi_vault lookup - add ``ansible_hashi_vault_auth_method`` Ansible vars entry to the ``proxies`` option (https://github.com/ansible-collections/community.hashi_vault/pull/86).
- hashi_vault lookup - add ``ansible_hashi_vault_ca_cert`` ansible var for ``ca_cert`` option (https://github.com/ansible-collections/community.hashi_vault/pull/97).
- hashi_vault lookup - add ``ansible_hashi_vault_namespace`` Ansible vars entry to the ``namespace`` option (https://github.com/ansible-collections/community.hashi_vault/pull/86).
- hashi_vault lookup - add ``ansible_hashi_vault_proxies`` Ansible vars entry to the ``proxies`` option (https://github.com/ansible-collections/community.hashi_vault/pull/86).
- hashi_vault lookup - add ``ansible_hashi_vault_role_id`` Ansible vars entry to the ``proxies`` option (https://github.com/ansible-collections/community.hashi_vault/pull/86).
- hashi_vault lookup - add ``ansible_hashi_vault_secret_id`` Ansible vars entry to the ``proxies`` option (https://github.com/ansible-collections/community.hashi_vault/pull/86).
- hashi_vault lookup - add ``ansible_hashi_vault_token_file`` Ansible vars entry to the ``token_file`` option (https://github.com/ansible-collections/community.hashi_vault/pull/95).
- hashi_vault lookup - add ``ansible_hashi_vault_token_path`` Ansible vars entry to the ``token_path`` option (https://github.com/ansible-collections/community.hashi_vault/pull/95).
- hashi_vault lookup - add ``ansible_hashi_vault_token_validate`` Ansible vars entry to the ``proxies`` option (https://github.com/ansible-collections/community.hashi_vault/pull/86).
- hashi_vault lookup - add ``ansible_hashi_vault_token`` Ansible vars entry to the ``proxies`` option (https://github.com/ansible-collections/community.hashi_vault/pull/86).
- hashi_vault lookup - add ``ansible_hashi_vault_url`` and ``ansible_hashi_vault_addr`` Ansible vars entries to the ``url`` option (https://github.com/ansible-collections/community.hashi_vault/pull/86).
- hashi_vault lookup - add ``ansible_hashi_vault_validate_certs`` Ansible vars entry to the ``validate_certs`` option (https://github.com/ansible-collections/community.hashi_vault/pull/95).
- hashi_vault lookup - add ``ca_cert`` INI config file key ``ca_cert`` option (https://github.com/ansible-collections/community.hashi_vault/pull/97).
- hashi_vault lookup - add ``none`` auth type which allows for passive auth via a Vault agent (https://github.com/ansible-collections/community.hashi_vault/pull/80).

Deprecated Features
-------------------

- hashi_vault collection - support for Python 2 will be dropped in version ``2.0.0`` of ``community.hashi_vault`` (https://github.com/ansible-collections/community.hashi_vault/issues/81).

v1.1.3
======

Release Summary
---------------

This release fixes a bug with ``userpass`` authentication and ``hvac`` versions 0.9.6 and higher.

Bugfixes
--------

- hashi_vault - userpass authentication did not work with hvac 0.9.6 or higher (https://github.com/ansible-collections/community.hashi_vault/pull/68).

v1.1.2
======

Release Summary
---------------

This release contains the same functionality as 1.1.1. The only change is to mark some code as internal to the collection. If you are already using 1.1.1 as an end user you do not need to update.

v1.1.1
======

Release Summary
---------------

This bugfix release restores the use of the ``VAULT_ADDR`` environment variable for setting the ``url`` option.
See the PR linked from the changelog entry for details and workarounds if you cannot upgrade.

Bugfixes
--------

- hashi_vault - restore use of ``VAULT_ADDR`` environment variable as a low preference env var (https://github.com/ansible-collections/community.hashi_vault/pull/61).

v1.1.0
======

Release Summary
---------------

This release contains a new ``proxies`` option for the ``hashi_vault`` lookup.

Minor Changes
-------------

- hashi_vault - add ``proxies`` option (https://github.com/ansible-collections/community.hashi_vault/pull/50).

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

