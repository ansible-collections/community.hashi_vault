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

General changes
===============

This section will cover some general differences not related to specific scenarios.

Options: direct vs. term string
-------------------------------

For a long time, the ``hashi_vault`` lookup took all of its options as ``name=value`` strings inside the term string, so you would do a lookup with a single string that looked something like ``secret/data/path auth_method=userpass username=my_user password=somepass``.

This way of passing options is discouraged, and ``hashi_vault`` was updated (before this collection existed) to support passing options as individual keyword arguments. The term string method was kept for backward compatibility.

.. note::

    None of the other lookups in this collection will support the old style term string syntax, so changing to direct options is highly recommended.

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
          - "Variables: {{ lookup('community.hashi_vault.hashi_vault', mount ~ '/data/' ~ path ~ ' auth_method=userpass username=' ~ user ~ ' password=' ~ pass) }}"
          #                                          note these necessary but easy to miss spaces ^                                          ^

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


Key dereferencing
-----------------

For these examples we will assume our result dictionary has this structure:

.. code-block:: yaml

    key_1: value1
    'key-2': 2
    'key three': three


``hashi_vault`` also supported a dictionary dereferencing syntax with colon ``:``, so it was common to see this:

.. code-block:: yaml+jinja

    - ansible.builtin.debug:
        msg:
          - "KV1 (key1): {{ lookup('community.hashi_vault.hashi_vault', 'kv1_mount/path/to/secret:key_1') }}"
          - "KV2 (key1): {{ lookup('community.hashi_vault.hashi_vault', 'kv2_mount/data/path/to/secret:key_1') }}"

With the above syntax, only the *value* of ``key_1`` is returned. Note that ``key three`` could not have been retrieved this way, because the space was the delimiter for the term string options.

.. note::

    The colon ``:`` syntax is not supported in any other lookups in the collection, and its use is discouraged.

**Colon** ``:`` **use does not correspond to any server-side filtering or other optimization**, so other than compact syntax there is there no advantage to using it.

The colon ``:`` syntax could always have been replaced by directly dereferencing in the Jinja2 template. Direct dereferencing can be done with the Jinja2 dot ``.`` syntax (which has restrictions on the key names) or via square brackets ``[]``, like so (KV version does not matter):

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

This looks a lot better, and it is from a readability perspective, but **in fact it will operate exactly the same way**, making a new request on every reference to ``secret``. This is due to lazy template evaluation in Ansible, and is discussed in more detail in the :ref:`lookup guide <ansible_collections.community.hashi_vault.docsite.lookup_guide>`. This can be remedied by either using ``ansible.builtin.set_fact`` to set the ``secret`` variable, or by using a module to do the read.

If you have extensive use of the colon ``:`` syntax, updating it before moving onto other plugins is recommended.

Return format
-------------

.. note::

    The ``return_format`` option will not be supported in other plugins. It is recommended to replace it with Jinja2 if you are using it currently.

The ``hashi_vault`` lookup takes a ``return_format`` option that defaults to ``dict``. The lookup always looks for a ``data`` field (see the :ref:`KV response details <ansible_collections.community.hashi_vault.docsite.migration_hashi_vault_lookup.kv_response>` for more information), and that is what is returned by default.

The ``raw`` value for ``return_format`` gives the raw API response from the request. This can be used to get the metadata from a KV2 request for example, which is usually stripped off, or it can be used to read from a non-KV path whose response happens to look like a KV response (with one or more ``data`` structures), and gets interpreted as one as a result.

For reading non-KV paths :ref:`other options are available <ansible_collections.community.hashi_vault.docsite.migration_hashi_vault_lookup.non_kv_replacements>`.

For getting access to KV2 metadata, see the section on :ref:`KV replacements <ansible_collections.community.hashi_vault.docsite.migration_hashi_vault_lookup.kv_replacements>`.

The ``return_format`` option can also be set to ``values`` to return a list of the dictionary's values.

This can be replaced with Jinja2. We will use our example secret again:

.. code-block:: yaml

    key_1: value1
    'key-2': 2
    'key three': three

And look at uses with ``return_format``:

.. code-block:: yaml+jinja

    # show a list of values, ['value1', 2, 'three']
    - ansible.builtin.debug:
        msg:
          - "KV1: {{ lookup('community.hashi_vault.hashi_vault', 'kv1_mount/path/to/secret', return_format='values') }}"

    # run debug once for each value
    - ansible.builtin.debug:
        msg: "{{ item }}"
      loop: "{{ query('community.hashi_vault.hashi_vault', 'kv1_mount/path/to/secret', return_format='values') }}"

We can do the same with Jinja2:

.. code-block:: yaml+jinja

    # show a list of values
    - ansible.builtin.debug:
        msg:
          - "KV1: {{ lookup('community.hashi_vault.hashi_vault', 'kv1_mount/path/to/secret').values() | list }}"

    # run debug once for each value
    - ansible.builtin.debug:
        msg: "{{ item }}"
      loop: "{{ lookup('community.hashi_vault.hashi_vault', 'kv1_mount/path/to/secret').values() | list }}"


Vault KV reads
==============

The most common use for the ``hashi_vault`` lookup is reading secrets from the KV secret store.

.. code-block:: yaml+jinja

    - ansible.builtin.debug:
        msg:
          - "KV1: {{ lookup('community.hashi_vault.hashi_vault', 'kv1_mount/path/to/secret') }}"
          - "KV2: {{ lookup('community.hashi_vault.hashi_vault', 'kv2_mount/data/path/to/secret') }}"

The return value of both of those is the dictionary of the key/value pairs in the secret, with no additional information from the API response, nor the metadata (in the case of KV2).

.. _ansible_collections.community.hashi_vault.docsite.migration_hashi_vault_lookup.kv_response:

KV1 and KV2 response structure
------------------------------

Under the hood, the return format of version 1 and version 2 of the KV store differs.

Here is a sample KV1 response:

.. code-block:: json

    {
        "auth": null,
        "data": {
            "Key1": "val1",
            "Key2": "val2"
        },
        "lease_duration": 2764800,
        "lease_id": "",
        "renewable": false,
        "request_id": "e26a7521-e512-82f1-3998-7cc494f14e86",
        "warnings": null,
        "wrap_info": null
    }

And a sample KV2 response:

.. code-block:: json

    {
        "auth": null,
        "data": {
            "data": {
                "Key1": "val1",
                "Key2": "val2"
            },
            "metadata": {
                "created_time": "2022-04-21T15:56:58.8525402Z",
                "custom_metadata": null,
                "deletion_time": "",
                "destroyed": false,
                "version": 2
            }
        },
        "lease_duration": 0,
        "lease_id": "",
        "renewable": false,
        "request_id": "15538d55-0ad9-1c39-2f4b-dcbb982f13cc",
        "warnings": null,
        "wrap_info": null
    }

The ``hashi_vault`` lookup traditionally returned the ``data`` field of whatever it was reading, and then later the plugin was updated to its current behavior, where it looks for the nested ``data.data`` structure, and if found, it returns only the inner ``data``. This aims to always return the secret data from KV1 and KV2 in a consistent format, but it means any additional information from KV2's metadata could not be accessed.

KV1 and KV2 API paths
---------------------

KV1's API path had the secret paths directly concatenated to the mount point. So for example, if a KV1 engine is mounted at ``kv/v/1`` (mount paths can contain ``/``), and a secret was created in that store at ``app/deploy_key``, the path would be ``kv/v/1/app/deploy_key``.

In KV2, there are separate paths that deal with the data and the metadata of a secret, so an additional ``/data/`` or ``/metadata/`` component needs to be inserted between the mount and the path.

For example with a KV2 store mounted at ``kv/v/2``, and a secret at ``app/deploy_key``, the path to read the secret data is ``kv/v/2/data/app/deploy_key``. For metadata operations it would be ``kv/v/2/metadata/app/deploy_key``.

Since ``hashi_vault`` does a generic read to an API path, anyone using it must know to insert those into the path, which causes a lot of confusion.

KV2 secret vesions
------------------

Since KV2 is a versioned secret store, multiple versions of the same secret usually exist. There was no dedicated way to get anything but the latest secret (default) with the ``hashi_vault`` lookup, but docs suggested that ``?version=2`` could be added to the path to get secret version 2. This did work but it directly modified the API path, so it was not considered a stable option. The dedicated KV2 content in the collection supports this as a first class option.


.. _ansible_collections.community.hashi_vault.docsite.migration_hashi_vault_lookup.kv_replacements:

KV get replacements
-------------------

As of collection version 2.5.0, the ``vault_kv1_get`` and ``vault_kv2_get`` lookups and modules were added:

  * ``vault_kv1_get`` :ref:`lookup <ansible_collections.community.hashi_vault.vault_kv1_get_lookup>`
  * ``vault_kv2_get`` :ref:`lookup <ansible_collections.community.hashi_vault.vault_kv2_get_lookup>`
  * ``vault_kv1_get`` :ref:`module <ansible_collections.community.hashi_vault.vault_kv1_get_module>`
  * ``vault_kv2_get`` :ref:`module <ansible_collections.community.hashi_vault.vault_kv2_get_module>`

These dedicated plugins clearly separate KV1 and KV2 operations. This ensures their behavior is clear and predictable.

As it relates to API paths, these plugins take the approach of most Vault client libraries, and recommended by HashiCorp, which is to accept the mount point as an option (``engine_mount_point``), separate from the path to be read. This ensures a proper path will be constructed internally, and does not require the caller to insert ``/data/`` on KV2.

For return values, the KV plugins no longer return a direct secret. Instead, the return values from KV1 and KV2, and both the module and lookup forms, have been unified to give easy access to the secret, the full API response, and other parts of the response discretely.

The return values are covered directly in the documentation for each plugin in the return and examples sections.

Examples
--------

Here are some before and after KV examples.

We will go back to our sample secret:

.. code-block:: yaml

    key_1: value1
    'key-2': 2
    'key three': three

And some usage:

.. code-block:: yaml+jinja

    - name: Reading secrets with hashi_vault and colon dereferencing
      ansible.builtin.debug:
        msg:
          - "KV1 (key1): {{ lookup('community.hashi_vault.hashi_vault', 'kv1_mount/path/to/secret:key_1') }}"
          - "KV2 (key1): {{ lookup('community.hashi_vault.hashi_vault', 'kv2_mount/data/path/to/secret:key_1') }}"

    - name: Replacing the above
      ansible.builtin.debug:
        msg:
          - "KV1 (key1): {{ lookup('community.hashi_vault.vault_kv1_get', 'path/to/secret', engine_mount_point='kv1_mount').secret.key_1 }}"
          - "KV2 (key1): {{ lookup('community.hashi_vault.vault_kv2_get', 'path/to/secret', engine_mount_point='kv2_mount').secret.key_1 }}"

    - name: Reading secret version 7 (old)
      ansible.builtin.debug:
        msg:
          - "KV2 (v7): {{ lookup('community.hashi_vault.hashi_vault', 'kv2_mount/data/path/to/secret?version=7') }}"

    - name: Reading secret version 7 (new)
      ansible.builtin.debug:
        msg:
          - "KV2 (v7): {{ lookup('community.hashi_vault.vault_kv2_get', 'path/to/secret', engine_mount_point='kv2_mount', version=7).secret }}"

    - name: Reading KV2 metadata (old)
      ansible.builtin.debug:
        msg:
          - "KV2 (metadata): {{ lookup('community.hashi_vault.hashi_vault', 'kv2_mount/data/path/to/secret', return_format='raw').data.metadata }}"

    - name: Reading KV2 metadata (new)
      ansible.builtin.debug:
        msg:
          - "KV2 (metadata): {{ lookup('community.hashi_vault.vault_kv2_get', 'path/to/secret', engine_mount_point='kv2_mount').metadata }}"


.. _ansible_collections.community.hashi_vault.docsite.migration_hashi_vault_lookup.non_kv_replacements:

General reads (non-KV)
======================

Since the ``hashi_vault`` lookup does a generic read internally, it can be used to read other paths that are not KV-specifc, for example reading from a cubbyhole or retrieving an AppRole's role ID.

More specific-purpose content is expected in the future, for example plugins for retrieving a role ID, but for anything not covered right now, we have the ``vault_read`` lookup and module:

  * ``vault_read`` :ref:`lookup <ansible_collections.community.hashi_vault.vault_read_lookup>`
  * ``vault_read`` :ref:`module <ansible_collections.community.hashi_vault.vault_read_module>`

These always do a direct read, and return a raw result, without trying to do any additional interpretation of the response. See their documentation for examples.
