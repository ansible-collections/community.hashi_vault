.. _ansible_collections.community.hashi_vault.docsite.localenv_developer_guide:

************************
localenv developer guide
************************

A "localenv" role in this collection sets up the external dependencies required to run the integration tests. The idea is to provide a pre-packaged way for a contributor to set up their local environment in a consistent, repeatable way.

..  note::

  This guide is a work-in-progress and is **very** light on details. For the time being, it's best to open an issue in the repository to discuss it if you're thinking of a new localenv. Looking at ``setup_localenv_docker`` should also be helpful as it's the most complete one to date.


.. contents::
  :local:
  :depth: 2


Required external dependencies
==============================

HashiCorp Vault
---------------

A Vault server is required for the integration tests. Using `Vault Dev Server Mode <https://www.vaultproject.io/docs/concepts/dev-server>`_ is recommended as it's the easiest and fastest way to get a server started.

A unencrypted (plain HTTP) listener is *required* for our purposes as most of the tests will expect to connect that way.

To run the tests that deal specifically with TLS/HTTPS access, you must start the Vault server with a TLS enabled listener. The TLS address:port, and the CA cert (or the cert itself if self-signed) must be supplied.

The **root token** of the Vault server is needed, as the integration tests make changes to Vault's configuration, and expect to have that token available to do so. It's possible to let Vault generate the token on startup and then retrieve it but it may be easiest to pre-generate one and pass it into Vault, via the ``-dev-root-token-id`` option or ``VAULT_DEV_ROOT_TOKEN_ID`` environment variable (see `Dev Options <https://www.vaultproject.io/docs/commands/server#dev-options>`_).

Relevant ``integration_config.yml`` variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. csv-table::
  :header: "var", "example", "description"
  :widths: 15, 20, 65

  "``vault_test_server_http``", "``http://myvault:8200``", "The full HTTP URL of your Vault test server."
  "``vault_test_server_https``", "``https://myvault:8300``", "The full HTTPS URL of your Vault test server."
  "``vault_dev_root_token_id``", "``3ee9a1f7-f115-4f7c-90a3-d3c73361bcb5``", "The root token used to authenticate to Vault."
  "``vault_version``", "``1.7.3``", "The desired version of Vault to download (only used by legacy setup). Can use the value ``latest``."
  "``vault_integration_legacy``", "``false``", "When ``true`` legacy integration will be used (see legacy section)."
  "``vault_cert_content``", "``-----BEGIN CERTIFICATE-----<snip>``", "The public cert of the CA that signed the cert used for Vault's TLS listener (or the cert itself if self-signed)."


Proxy server
------------

A proxy server is used to test the proxy connectivity options.

In theory any proxy supporting http/s targets could be used for this purpose, but `tinyproxy <https://github.com/tinyproxy/tinyproxy>`_ is recommended for being, well.. tiny, as well as easy to configure and run, and available in package managers and containers.

Relevant ``integration_config.yml`` variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. csv-table::
  :header: "var", "example", "description"
  :widths: 15, 20, 65

  "``vault_proxy_server``", "``http://proxy:8080``", "The full HTTP URL of your proxy server."

localenv role conventions
=========================

* Use ``files/.output`` to hold generated artifacts.
* Anything generated should be in a ``.gitignore``; conversely anything not in a ``.gitignore`` should not be overwritten or modified by this process. That is, there should be no changes to git status that arise from this.
* Consider providing a ``setup.sh`` to avoid having to manually run ``ansible-`` commands. It should ideally operate correctly regardless of the current working directory.
* Generate a usable ``integration_config.yml`` that allows for using the result of the localenv. Generate it within the role output, not outside the role. Copy it to the right location, but do not overwrite an existing one.
* If the role has external dependencies, try to codify those in file(s) that can be used by the right tool, like ``requirements.yml`` for ``ansible-galaxy``, etc.
* localenv roles are meant to run **outside** of the ``ansible-test`` environment, but they can make (re)use of other roles; for example a localenv that seeks to run Vault directly on the local machine could reuse the setup roles for downloading and launching Vault that are used (within the test environment) by the legacy integration.
