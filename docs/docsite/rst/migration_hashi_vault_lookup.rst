.. _ansible_collections.community.hashi_vault.docsite.migration_hashi_vault_lookup:

*****************************************
Migrating from the ``hashi_vault`` lookup
*****************************************

This is a guide for migrating from the ``hashi_vault`` :ref:`lookup plugin <ansible_collections.community.hashi_vault.hashi_vault_lookup>` to newer content in this collection.

To understand why, please see :ref:`this page describing the plugin's history and future <ansible_collections.community.hashi_vault.docsite.about_hashi_vault_lookup>`.

.. contents::
  :local:
  :depth: 2

A note about lookups vs. modules
================================

Since the ``hashi_vault`` plugin is a lookup, it is often most straightforward to replace its use with other lookups. There was no module option available previously, however there is now.

Although it may be more involved, consider each use case to determine if a module is more appropriate.

For more information, see the :ref:`lookup guide <ansible_collections.community.hashi_vault.docsite.lookup_guide>`.

Options: direct vs. term string
===============================

For a long time, the ``hashi_vault`` lookup took all of its options as ``name=value`` strings inside the term string, so you would do a lookup with a single string that looked something like ``secret/data/path auth_method=userpass username=my_user password=somepass``.

This way of passing options is discouraged, and ``hashi_vault`` was updated (before this collection existed) to support passing options as individual keyword arguments. The term string method was kept for backward compatibility.

.. note::

    None of the other lookups in this collection will support the old style term string syntax, so it's highly recommended to change that.

If your existing lookups use options in the term string, you may want to first change to direct use of options before trying to change the plugin, **especially if you intend to continue using lookups instead of modules**.

Examples of the term string style:

.. code-block:: yaml+jinja

    - name: Term string style
      vars:
        user: my_user
        pass: '{{ my_secret_password }}'
        mount: secret
        relpath: path
      ansible.builtin.debug:
        msg:
          - "Static: {{ lookup('community.hashi_vault.hashi_vault', 'secret/data/path auth_method=userpass username=my_user password=somepass') }}"
          - "Variables: {{ lookup('community.hashi_vault.hashi_vault', mount ~ '/data/' ~ path ~ 'auth_method=userpass username=' ~ user ~ 'password=' ~ pass) }}"

And the same lookups converted to direct options:

.. code-block:: yaml+jinja

    - name: Direct option style
      vars:
        user: my_user
        pass: '{{ my_secret_password }}'
        mount: secret
        relpath: path
      ansible.builtin.debug:
        msg:
          - "Static: {{ lookup('community.hashi_vault.hashi_vault', 'secret/data/path', auth_method='userpass', username='my_user', password='somepass') }}"
          - "Variables: {{ lookup('community.hashi_vault.hashi_vault', mount ~ '/data/' ~ path, auth_method='userpass', username=user, password=pass) }}"


Vault KV reads
==============

The most common use for the ``hashi_vault`` lookup is reading secrets from the KV secret store.

.. code-block:: yaml+jinja

    - ansible.builtin.debug:
        msg:
          - "KV1: {{ lookup('community.hashi_vault.hashi_vault', 'kv1_mount/path/to/secret') }}"
          - "KV2: {{ lookup('community.hashi_vault.hashi_vault', 'kv2_mount/data/path/to/secret') }}"

The return value of both of those is the dictionary of the key/value pairs in the secret, with no additional information from the API response, nor the metadata (in the case of KV2).

For these examples we will assume our secret has this structure:

.. code-block:: yaml

    key_1: value1
    'key-2': 2
    'key three': three

Key dereferencing
-----------------

``hashi_vault`` also supported a dictionary dereferencing syntax with colon ``:``, so this was also common:

.. code-block:: yaml+jinja

    - ansible.builtin.debug:
        msg:
          - "KV1 (key1): {{ lookup('community.hashi_vault.hashi_vault', 'kv1_mount/path/to/secret:key_1') }}"
          - "KV2 (key1): {{ lookup('community.hashi_vault.hashi_vault', 'kv2_mount/data/path/to/secret:key_1') }}"

With the above syntax, only the *value* of ``key_1`` is returned. Note that ``key three`` could not have been retrieved this way, because the space was the delimiter for the term string options.

.. note::

    The colon ``:`` syntax is not supported in any other lookups in the collection, and use is discouraged.

The colon ``:`` syntax could always have been replaced by directly dereferencing in the Jinja2 template. ``:`` use does not correspond to any server-side filtering or other optimization, so other than compact syntax there is there no advantage to using it.

Direct dereferencing can be done with the dot ``.`` syntax (which has restrictions on the key names) or via square brackets ``[]``, like so (KV version does not matter):

.. code-block:: yaml+jinja

    - vars:
        k1: key_1
        k2: key-2
        k3: key three
      ansible.builtin.debug:
        msg:
          - "KV1 (key1, dot): {{ lookup('community.hashi_vault.hashi_vault', 'kv1_mount/path/to/secret').key_1 }}"
          - "KV1 (key1, [ ]): {{ lookup('community.hashi_vault.hashi_vault', 'kv1_mount/path/to/secret')['key_1'] }}"
          - "KV1 (var1, [ ]): {{ lookup('community.hashi_vault.hashi_vault', 'kv1_mount/path/to/secret')[k1] }}"
          - "KV1 (key2, [ ]): {{ lookup('community.hashi_vault.hashi_vault', 'kv1_mount/path/to/secret')['key-2'] }}"
          - "KV1 (var2, [ ]): {{ lookup('community.hashi_vault.hashi_vault', 'kv1_mount/path/to/secret')[k2] }}"
          - "KV1 (key3, [ ]): {{ lookup('community.hashi_vault.hashi_vault', 'kv1_mount/path/to/secret')['key three'] }}"
          - "KV1 (var3, [ ]): {{ lookup('community.hashi_vault.hashi_vault', 'kv1_mount/path/to/secret')[k3] }}"

Note that only ``key_1`` could use the dot ``.`` syntax because the allowed characters for that are limited to those allowed for Python symbols. Variables also cannot be used with dot ``.`` access.

Furthermore, the colon ``:`` syntax encouraged multiple lookups to the same secret only for the purpose of getting different keys, leading to multiple identical requests to Vault. **The above example also suffers from this**.

A more DRY approach might look like this:

.. code-block:: yaml+jinja

    - vars:
        secret: "{{ lookup('community.hashi_vault.hashi_vault', 'kv1_mount/path/to/secret') }}"
        k1: key_1
        k2: key-2
        k3: key three
      ansible.builtin.debug:
        msg:
          - "KV1 (key1, dot): {{ secret.key_1 }}"
          - "KV1 (key1, [ ]): {{ secret['key_1'] }}"
          - "KV1 (var1, [ ]): {{ secret[k1] }}"
          - "KV1 (key2, [ ]): {{ secret['key-2'] }}"
          - "KV1 (var2, [ ]): {{ secret[k2] }}"
          - "KV1 (key3, [ ]): {{ secret['key three'] }}"
          - "KV1 (var3, [ ]): {{ secret[k3] }}"

This looks a lot better, and it is from a readability perspective, but **in fact it will operate exactly the same way**, making a new request on every reference to ``secret``. This is due to lazy template evaluation in Ansible, and is discussed in more detail in the :ref:`lookup guide <ansible_collections.community.hashi_vault.docsite.lookup_guide>`.

If you have extensive use of the colon ``:`` syntax, updating it before
