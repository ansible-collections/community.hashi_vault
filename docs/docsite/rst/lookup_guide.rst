.. _ansible_collections.community.hashi_vault.docsite.lookup_guide:

************
Lookup guide
************

This guide is not a comprehensive listing of included lookup plugins and how to use them, rather it is intended to explain the role of the lookup plugins in ``community.hashi_vault`` and how they are they used, especially when compared to modules of the same name.

.. contents::
  :local:
  :depth: 2


About the ``hashi_vault`` lookup
================================

The ``hashi_vault`` lookup plugin is the oldest Vault-related content in Ansible. It was included in pre-collections Ansible (<2.10). As a result, it's the most used plugin for Vault, and the one most people are familiar with.

``hashi_vault`` lookup considerations
-------------------------------------

Due to the history of the ``hashi_vault`` lookup plugin, it does many jobs. It is versatile, but sometimes unintuitive.

The ``hashi_vault`` lookup plugin performs three main tasks:

- authentication, taking parameters for various login types, performing a login, and acquiring a token with which it can make additional calls to Vault.
- a generic read operation, which allows it to read any kind of Vault path, without having to be written with that type of path in mind.
- transforming responses that look like ``kv2`` responses into simpler responses that resemble those from ``kv1``.

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

Since reading from ``kv`` store is by far the most common use case, we will also be introducing content for that specifically, which will accept familiar paths and provide parameters for ``kv``-specific functionality like versioning. That content is coming soon.

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

Lookups and writes
==================


Most Ansible lookups perform read-only, non-destructive operations. They are run in templating, they generally *return*  values, and they **do not run differently in check mode** (that is they do the same thing they would in normal mode, even if that means changing something). However, some lookups do change state, sometimes by performing write operations. For example, the ``password`` :ref:`lookup <ansible_collections.ansible.builtin.password_lookup>` writes a generated password to a file, to act as a sort of cache, and the ``pipe`` :ref:`lookup <ansible_collections.ansible.builtin.pipe_lookup>` runs an arbitrary shell command so it could easily write or change state.

Writes in Vault
---------------

Operations that perform writes in Vault are not limited to the obvious ones such as writing a secret value, creating a policy, or enabling a new auth method.

Any operation that creates a token for example, such as any login operation, is also a write; tokens use storage in Vault and having too many active tokens is a common cause of performance problems.

Additionally, some values in Vault can only be "read" at the moment of their creation, and so the only way to retrieve such a value, is to get it as a response from the "write" that created it. A common example is AppRole secret IDs.

The way this relates to Ansible and this collection, is that we may have lookup plugins that either unintuitively perform writes (like ``vault_login``), or appear inappropriate to exist as lookups in the first place, like the planned ``vault_write`` lookup.

The reason for this is that the we often consider these operations to be logical "read" operations, like performing a login, and want to use their results in other expressions.

Something like ``vault_write`` does not always fit that description, because you could use it in a way that is clearly an explicit write, for example you could create a new policy with the lookup. But there are times it may be appropriate to use it in lookup semantics, like when "retrieving" (really creating) a new secret ID for an approle.

When considering built-in support for auth methods, any auth method other than ``token`` or ``none`` makes every lookup, even ``vault_read``, into something that's changing state and performing a write within Vault. This actually applies to many modules too, even when using check mode.

How to reason about when to use lookups
---------------------------------------

Because there is potential for writes in any lookup, it is very important to carefully consider when you are using a lookup vs. a module/other plugin. Check mode has no effect on lookups, so there is potential to perform many writes within your check mode run, but maybe sometimes you want that, for example if you're performing a ``vault_login`` via lookup to retrieve a token to use in your module calls, you may want that to still happen in check mode so that your module calls can properly check the things they need to.

Some modules that are read focused, like the ``vault_read`` module, when used with auth other than ``token`` or ``none``, will still perform an internal login even in check mode, so this is still another consideration.

Lookups and lazy templating
---------------------------

The capacity for lookups to perform writes or change state is exacerbated by Ansible's "lazy" templating, if not used carefully.

Consider the following example:

.. code-block:: yaml+jinja

    - vars:
        token: "{{ lookup('community.hashi_vault.vault_login', auth_method='userpass', username='user', password='pass') | community.hashi_vault.vault_login_token }}"
        secret: "{{ lookup('community.hashI_vault.vault_read', 'secrets/data/my-secret', token=token) }}"
        value_a: "{{ secret.data.data.a }}"
        value_b: "{{ secret.data.data.b }}"
      ansible.builtin.debug:
        msg: "Secret value A is '{{ value_a }}' while value B is '{{ value_b }}'."

Since templating is recursive and evaluated lazily, this will unfortunately *not* result in a single login, reusing the token to perform a single secret read, which is then used is dictionary lookups.

Instead, evaluation of ``value_a`` and ``value_b`` will *each* cause separate evaluation of ``secret``, so that lookup will be performed twice, and *each of those lookups* will cause a separate evaluation of ``token``, which will perform two separate logins, resulting in two tokens being created, and two reads of the exact same secret being performed.

If you combine this with loops, or reusing vars over multiple tasks, you can very quickly multiply the number of requests being made to Vault, and in the case of writes, the number of objects being created.

Tasks can be better for this, since they execute when encountered without being accidentally repeated, and the values they return are static.

.. code-block:: yaml+jinja

    - name: login
      community.hashi_vault.vault_login:
        auth_method: userpass
        username: user
        password: pass
      register: login

    - name: get secret
      community.hashi_vault.vault_read:
        token: '{{ login | community.hashi_vault.vault_login_token }}'
        path: 'secrets/data/my-secret'
      register: secret

    - vars:
        value_a: "{{ secret.data.data.data.a }}"
        value_b: "{{ secret.data.data.data.b }}"
      ansible.builtin.debug:
        msg: "Secret value A is '{{ value_a }}' while value B is '{{ value_b }}'."

This example will do a single login and secret lookup, even though it is more verbose. It also means the ``secret`` and ``login`` variables can be re-used in more tasks without performing additional requests to Vault.

Another thing to consider in both of the examples is that tasks run *per host*, so you may be multiplying the requests yet again.

In the lookup example, those requests all happen on the controller, and in the module example, they happen on the remote host unless the play is targeted locally.

In both cases, you may *want* to make those requests per host, because some of the variables involved in the lookups may rely on per-host values, like differing authentication, different secret paths, even different Vault servers altogether, or in the case of certain access restrictions, you may need the remote host to make the connection rather than the controller.

But if all of your secret access is intended to be from the controller, and the requests do not depend on host-level variables, you can potentially cut your requests by a lot, by using ``run_once``, or making Vault calls in a separate play that only targets ``localhost`` and using ``set_fact``, or via other methods.
