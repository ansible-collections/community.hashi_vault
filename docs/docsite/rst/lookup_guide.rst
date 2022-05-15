.. _ansible_collections.community.hashi_vault.docsite.lookup_guide:

************
Lookup guide
************

This guide is not a comprehensive listing of included lookup plugins and how to use them, rather it is intended to explain the role of the lookup plugins in ``community.hashi_vault`` and how they are they used, especially when compared to modules of the same name.

For information about the ``hashi_vault`` lookup specifically, see :ref:`this page that covers it in detail <ansible_collections.community.hashi_vault.docsite.about_hashi_vault_lookup>`.

.. contents::
  :local:
  :depth: 2


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
        secret: "{{ lookup('community.hashi_vault.vault_read', 'secrets/data/my-secret', token=token) }}"
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

In the lookup example, those requests all happen on the controller, and in the module example, they happen on the remote host unless the play or task is targeted locally.

In both cases, you may *want* to make those requests per host, because some of the variables involved in the lookups may rely on per-host values, like differing authentication, different secret paths, even different Vault servers altogether, or in the case of certain access restrictions, you may need the remote host to make the connection rather than the controller.

But if all of your secret access is intended to be from the controller, and the requests do not depend on host-level variables, you can potentially cut your requests by a lot, by using ``run_once``, or making Vault calls in a separate play that only targets ``localhost`` and using ``ansible.builtin.set_fact``, or via other methods.
