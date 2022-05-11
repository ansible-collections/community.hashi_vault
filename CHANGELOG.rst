===================================
community.hashi_vault Release Notes
===================================

.. contents:: Topics


v2.5.0
======

Release Summary
---------------

This release finally contains dedicated KV plugins and modules, and an exciting new lookup to help use plugin values in module calls.
With that, we also have a guide in the collection docsite for migrating away from the ``hashi_vault`` lookup toward dedicated content.
We are also announcing that the ``token_validate`` option will change its default value in version 4.0.0.
This is the last planned release before 3.0.0. See the porting guide for breaking changes and removed features in the next version.

Minor Changes
-------------

- vault_login module & lookup - no friendly error message was given when ``hvac`` was missing (https://github.com/ansible-collections/community.hashi_vault/issues/257).
- vault_pki_certificate - add ``vault_pki_certificate`` to the ``community.hashi_vault.vault`` action group (https://github.com/ansible-collections/community.hashi_vault/issues/251).
- vault_read module & lookup - no friendly error message was given when ``hvac`` was missing (https://github.com/ansible-collections/community.hashi_vault/issues/257).
- vault_token_create - add ``vault_token_create`` to the ``community.hashi_vault.vault`` action group (https://github.com/ansible-collections/community.hashi_vault/issues/251).
- vault_token_create module & lookup - no friendly error message was given when ``hvac`` was missing (https://github.com/ansible-collections/community.hashi_vault/issues/257).
- vault_write - add ``vault_write`` to the ``community.hashi_vault.vault`` action group (https://github.com/ansible-collections/community.hashi_vault/issues/251).

Deprecated Features
-------------------

- token_validate options - the shared auth option ``token_validate`` will change its default from ``True`` to ``False`` in community.hashi_vault version 4.0.0. The ``vault_login`` lookup and module will keep the default value of ``True`` (https://github.com/ansible-collections/community.hashi_vault/issues/248).

New Plugins
-----------

Lookup
~~~~~~

- vault_ansible_settings - Returns plugin settings (options)
- vault_kv1_get - Get a secret from HashiCorp Vault's KV version 1 secret store
- vault_kv2_get - Get a secret from HashiCorp Vault's KV version 2 secret store

New Modules
-----------

- vault_kv1_get - Get a secret from HashiCorp Vault's KV version 1 secret store
- vault_kv2_get - Get a secret from HashiCorp Vault's KV version 2 secret store

v2.4.0
======

Release Summary
---------------

Our first content for writing to Vault is now live.

New Plugins
-----------

Lookup
~~~~~~

- vault_write - Perform a write operation against HashiCorp Vault

New Modules
-----------

- vault_write - Perform a write operation against HashiCorp Vault

v2.3.0
======

Release Summary
---------------

This release contains new plugins and modules for creating tokens and for generating certificates with Vault's PKI secrets engine.

New Plugins
-----------

Lookup
~~~~~~

- vault_token_create - Create a HashiCorp Vault token

New Modules
-----------

- vault_pki_generate_certificate - Generates a new set of credentials (private key and certificate) using HashiCorp Vault PKI
- vault_token_create - Create a HashiCorp Vault token

v2.2.0
======

Release Summary
---------------

This release contains a new lookup/module combo for logging in to Vault, and includes our first filter plugin.

Minor Changes
-------------

- The Filter guide has been added to the collection's docsite.

New Plugins
-----------

Filter
~~~~~~

- vault_login_token - Extracts the client token from a Vault login response

Lookup
~~~~~~

- vault_login - Perform a login operation against HashiCorp Vault

New Modules
-----------

- vault_login - Perform a login operation against HashiCorp Vault

v2.1.0
======

Release Summary
---------------

The most important change in this release is renaming the ``aws_iam_login`` auth method to ``aws_iam`` and deprecating the old name. This release also announces the deprecation of Ansible 2.9 and ansible-base 2.10 support in 3.0.0.

Deprecated Features
-------------------

- Support for Ansible 2.9 and ansible-base 2.10 is deprecated, and will be removed in the next major release (community.hashi_vault 3.0.0) next spring (https://github.com/ansible-community/community-topics/issues/50, https://github.com/ansible-collections/community.hashi_vault/issues/189).
- aws_iam_login auth method - the ``aws_iam_login`` method has been renamed to ``aws_iam``. The old name will be removed in collection version ``3.0.0``. Until then both names will work, and a warning will be displayed when using the old name (https://github.com/ansible-collections/community.hashi_vault/pull/193).

Removed Features (previously deprecated)
----------------------------------------

- the "legacy" integration test setup has been removed; this does not affect end users and is only relevant to contributors (https://github.com/ansible-collections/community.hashi_vault/pull/191).

v2.0.0
======

Release Summary
---------------

Version 2.0.0 of the collection drops support for Python 2 & Python 3.5, making Python 3.6 the minimum supported version.
Some deprecated features and settings have been removed as well.

Breaking Changes / Porting Guide
--------------------------------

- connection options - there is no longer a default value for the ``url`` option (the Vault address), so a value must be supplied (https://github.com/ansible-collections/community.hashi_vault/issues/83).

Removed Features (previously deprecated)
----------------------------------------

- drop support for Python 2 and Python 3.5 (https://github.com/ansible-collections/community.hashi_vault/issues/81).
- support for the following deprecated environment variables has been removed: ``VAULT_AUTH_METHOD``, ``VAULT_TOKEN_PATH``, ``VAULT_TOKEN_FILE``, ``VAULT_ROLE_ID``, ``VAULT_SECRET_ID`` (https://github.com/ansible-collections/community.hashi_vault/pull/173).

v1.5.0
======

Release Summary
---------------

This release includes a new action group for use with ``module_defaults``, and additional ways of specifying the ``mount_point`` option for plugins.
This will be the last ``1.x`` release.

Minor Changes
-------------

- add the ``community.hashi_vault.vault`` action group (https://github.com/ansible-collections/community.hashi_vault/pull/172).
- auth methods - Add support for configuring the ``mount_point`` auth method option in plugins via the ``ANSIBLE_HASHI_VAULT_MOUNT_POINT`` environment variable, ``ansible_hashi_vault_mount_point`` ansible variable, or ``mount_point`` INI section (https://github.com/ansible-collections/community.hashi_vault/pull/171).

v1.4.1
======

Release Summary
---------------

This release contains a bugfix for ``aws_iam_login`` authentication.

Bugfixes
--------

- aws_iam_login auth method - fix incorrect use of ``boto3``/``botocore`` that prevented proper loading of AWS IAM role credentials (https://github.com/ansible-collections/community.hashi_vault/issues/167).

v1.4.0
======

Release Summary
---------------

This release includes bugfixes, a new auth method (``cert``), and the first new content since the collection's formation, the ``vault_read`` module and lookup plugin.
We're also announcing the deprecation of the ``[lookup_hashi_vault]`` INI section (which will continue working up until its removal only for the ``hashi_vault`` lookup), to be replaced by the ``[hashi_vault_collection]`` section that will apply to all plugins in the collection.

Minor Changes
-------------

- community.hashi_vault collection - add cert auth method (https://github.com/ansible-collections/community.hashi_vault/pull/159).

Deprecated Features
-------------------

- lookup hashi_vault - the ``[lookup_hashi_vault]`` section in the ``ansible.cfg`` file is deprecated and will be removed in collection version ``3.0.0``. Instead, the section ``[hashi_vault_collection]`` can be used, which will apply to all plugins in the collection going forward (https://github.com/ansible-collections/community.hashi_vault/pull/144).

Bugfixes
--------

- aws_iam_login auth - the ``aws_security_token`` option was not used, causing assumed role credentials to fail (https://github.com/ansible-collections/community.hashi_vault/issues/160).
- hashi_vault collection - a fallback import supporting the ``retries`` option for ``urllib3`` via ``requests.packages.urllib3`` was not correctly formed (https://github.com/ansible-collections/community.hashi_vault/issues/116).
- hashi_vault collection - unhandled exception with ``token`` auth when ``token_file`` exists but is a directory (https://github.com/ansible-collections/community.hashi_vault/issues/152).

New Plugins
-----------

Lookup
~~~~~~

- vault_read - Perform a read operation against HashiCorp Vault

New Modules
-----------

- vault_read - Perform a read operation against HashiCorp Vault

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

