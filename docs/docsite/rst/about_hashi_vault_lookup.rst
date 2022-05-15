.. _ansible_collections.community.hashi_vault.docsite.about_hashi_vault_lookup:

********************************
About the ``hashi_vault`` lookup
********************************

This page explains the past, present, and future of the ``hashi_vault`` :ref:`lookup plugin <ansible_collections.community.hashi_vault.hashi_vault_lookup>`.

The ``hashi_vault`` lookup is the oldest Vault-related content in Ansible. It was included in pre-collections Ansible (<2.10). As a result, it's the most used plugin for Vault, and the one most people are familiar with.

At this time, we recommend using newer content in the collection, and we believe all use cases for ``hashi_vault`` have been covered by newer plugins. To understand the history, continue reading this document. For help with migration, :ref:`the hashi_vault migration guide <ansible_collections.community.hashi_vault.docsite.migration_hashi_vault_lookup>` has you covered.

.. contents::
  :local:
  :depth: 2

Synopsis
========

The short summary is:

* The ``hashi_vault`` lookup does several jobs and uses some patterns that we would like to change, but are well-entrenched.
* The ``community.hashi_vault`` collection is developing and releasing new plugins and modules that are more tightly-scoped and will offer individual coverage for many use cases that the ``hashi_vault`` lookup has been used for.
* At this time, there are no plans to deprecate the ``hashi_vault`` lookup, but it is also unlikely that it will receive new features specific to that lookup (improvements in shared code like new auth methods are included automatically).
* As more plugins are released in the collection, we will be adding specific migration guidance to this page with examples.

The long story
==============

``hashi_vault`` lookup considerations
-------------------------------------

Due to the history of the ``hashi_vault`` lookup plugin, it does many jobs. It is versatile, but sometimes unintuitive.

The ``hashi_vault`` lookup plugin performs three main tasks:

* authentication, taking parameters for various login types, performing a login, and acquiring a token with which it can make additional calls to Vault.
* a generic read operation, which allows it to read any kind of Vault path, without having to be written with that type of path in mind.
* transforming responses that look like ``kv2`` responses into simpler responses that resemble those from ``kv1``.

Reading secrets is the most common use case, with the ``kv`` (key/value) store built into Vault as by far the most common secret store. Most implementations use v2 of the ``kv`` store. To make reading v2 ``kv`` secrets easy, the lookup plugin assumes that you're probably trying to read a ``kv`` secret, and tries to infer if the response is from ``kv2``, because the responses from version 2 include metadata and have the secret value additionally wrapped in another structure. The lookup plugin seeks to make ``kv2`` responses look more like responses from version 1.

Since the ``kv`` store has one or more key/value pairs in each secret, the lookup also supports a non-standard suffix in its path that can be used to access a value belonging to one specific key, via the ``:keyname`` syntax. While this is useful to provide a compact way to access a single secret value (admittedly a very common use case), it complicates the implementation and leads to bad habits.

For example, it became common to see people use many lookup invocations with the same path, each with a different ``:keyname``, to access multiple values within a single secret, but this is quite wasteful, as it does a separate login and secret lookup, all to return the same value, and the key dereferencing is done client side. Further, dereferencing can be done directly in Jinja where it's more clear what's going on, using the ``.key`` or ``['key']`` syntax.

One last idiosyncrasy of the plugin is its support for supplying all of its parameters in the term string. This looks compact, but it greatly complicates the processing of plugin options. At the time that this lookup was created, many other lookups allowed options to be supplied in the term string, but it has since been considered an anti-pattern, and has been deprecated/removed from core plugins.

Another downside of this is that it prevents us from effectively re-using the authentication token in cases when multiple term strings are supplied, directly or via ``with_community.hashi_vault.hashi_vault``, and as a result this type of usage results in a new login for each term. In newer lookups, we can take advantage of a single login to perform multiple operations.

All of these considerations make sense in context, but it somewhat muddles the purpose of the lookup:

* If a response from a completely different endpoint ended up looking like a ``kv2`` response, it would return an unexpected result.
* If you try to give the path of a ``kv2`` secret directly, it will not work unless you insert a ``/data/`` component into the path, in order to match the *API path* rather than the path people are usually familiar with.
* If you want the metadata returned along with a ``kv2`` response, you cannot get it.
* Other features of ``kv2`` like secret versioning cannot directly be used, unless you modify the URL, which is error prone and unintuitive.
* Getting access to the token created by the internal login, in order to re-use it, is not possible.

How we are addressing the considerations
----------------------------------------

The built-in authentication support will be kept, and in fact it has been moved to shared utilities within the collection, so that all plguins and modules can share the functionality, and work consistently. That makes it easier to test new and existing auth methods, easier to add new ones (which automaticallly become part of all existing content), and easier to add new content, because authentication does not need to be reimplemented.

In addition, it is now possible to perform a login directly and return the token, for general re-use, via the ``community.hashi_vault.vault_login`` :ref:`module <ansible_collections.community.hashi_vault.vault_login_module>` and :ref:`lookup plugin <ansible_collections.community.hashi_vault.vault_login_lookup>`.

Generic read (not ``kv`` specific) is still important functionality, so we have the ``community.hashi_vault.vault_read`` :ref:`module <ansible_collections.community.hashi_vault.vault_read_module>` and :ref:`lookup plugin <ansible_collections.community.hashi_vault.vault_read_lookup>` to provide that without trying to infer whether the response is from a specific backend.

Since reading from the ``kv`` store is by far the most common use case, we have dedicated content for that:

* ``community.hashi_vault.vault_kv1_get`` :ref:`module <ansible_collections.community.hashi_vault.vault_kv1_get_module>`
* ``community.hashi_vault.vault_kv2_get`` :ref:`module <ansible_collections.community.hashi_vault.vault_kv2_get_module>`
* ``community.hashi_vault.vault_kv1_get`` :ref:`lookup <ansible_collections.community.hashi_vault.vault_kv1_get_lookup>`
* ``community.hashi_vault.vault_kv2_get`` :ref:`lookup <ansible_collections.community.hashi_vault.vault_kv2_get_lookup>`

The dictionary dereferencing via ``:keyname`` syntax *will not be supported* in other content. That will be achieved in Jinja via:

* dot syntax ``.keyname``
* lookup syntax ``['keyname']``
* specialized filters in some circumstances, such as the ``vault_login_token`` :ref:`filter <ansible_collections.community.hashi_vault.docsite.filter_guide.vault_login_token>`.

Parameters via term string *will not be supported* in other lookups. Its use is discouraged by core developers, and steps have already been taken in core to remove the functionality where it still exists, however it will remain in the ``hashi_vault`` plugin for backwards compatibility and because it is likely to still be in use in a lot of places.

The future of the ``hashi_vault`` lookup
----------------------------------------

There are no plans currently to deprecate or remove the ``hashi_vault`` plugin. It is likely that it will stay indefinitely, for backwards compatibility and because so much functionality has been moved to shared code that very little maintenance is required to keep it. This decision may be revisited if circumstances change.

That being said, we will encourage the use of newer content that has functionality with a tighter scope and is expected to receive updates and enchancements as appropriate.

New features and functionality are unlikely to be added or accepted in the ``hashi_vault`` lookup, except for the ones that come for "free", like new auth methods (these require no code changes to the plugin itself).
