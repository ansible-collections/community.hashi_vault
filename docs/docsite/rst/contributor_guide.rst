.. _ansible_collections.community.hashi_vault.docsite.contributor_guide:

*****************
Contributor guide
*****************

This guide aims to help anyone who wishes to contribute to the ``community.hashi_vault`` collection.

.. note::

	This guide can be improved with your help! Open a `GitHub issue in the repository <https://github.com/ansible-collections/community.hashi_vault/issues>`_ or contribute directly by following the instructions below.


.. contents::
  :local:
  :depth: 3


Quick start
===========

#. Log into your GitHub account.
#. Fork the `ansible-collections/community.hashi_vault repository <https://github.com/ansible-collections/community.hashi_vault>`_ by clicking the **Fork** button in the upper right corner. This will create a fork in your own account.
#. Clone the repository locally, following :ref:`the example instructions here <hacking_collections>` (but replace ``general`` with ``hashi_vault``). **Pay special attention to the local path structure** of the cloned repository as described in those instructions (for example ``ansible_collections/community/hashi_vault``).
#. As mentioned on that page, commit your changes to a branch, push them to your fork, and create a pull request (GitHub will automatically prompt you to do so when you look at your repository).
#. :ref:`See the guidance on Changelogs <community_changelogs>` and include a :ref:`changelog fragment <changelogs_how_to>` if appropriate.

Contributing documentation
==========================

Additions to the collection documentation are very welcome! We have three primary types of documentation, each with their own syntax and rules.

README and other markdown files
-------------------------------

Markdown files (those with the extension ``.md``) can be found in several directories within the repository. These files are primarily aimed at developers and those browsing the repository, to explain or give context to the other files nearby.

The main exception to the above is the ``README.md`` in the repository root. This file is more important because it provides introductory information and links for anyone browsing the repository, both on GitHub and on the collection's `Ansible Galaxy page <https://galaxy.ansible.com/community/hashi_vault>`_.

Markdown files can be previewed natively in GitHub, so they are easy to validate by reviewers, and there are no specific tests that need to run against them.

Your IDE or code editor may also be able to preview these files. For example `Visual Studio Code has built-in markdown preview <https://code.visualstudio.com/docs/languages/markdown#_markdown-preview>`_.

Module and plugin documentation
-------------------------------

This type of documentation gets generated from structured YAML, inside of a Python string. It is included in the same code that it's documenting, or in a separate Python file, such as a doc fragment. Please see the :ref:`module format and documentation guidance <developing_modules_documenting>` for more information.

This type of documentation is highly structured and tested with ``ansible-test sanity``. Full instructions are available on the :ref:`testing module documentation <testing_module_documentation>` page.

Additionally, the docsite build on pull requests (or built locally) will include module and plugin documentation as well. See the next section for details.

Collection docsite
------------------

The collection docsite is what you are reading now. It is written in reStructuredText (RST) format and published on the :ref:`ansible_documentation` site. This is where we have long-form documentation that doesn't fit into the other two categories.

If you are considering adding an entirely new document here it may be best to open a GitHub issue first to discuss the idea and how best to organize it.

Refer to the :ref:`Ansible style guide <style_guide>` for all submissions to the collection docsite.

RST files for the docsite are in the ``docs/docsite/rst/`` directory. Some submissions may also require edits to ``docs/docsite/extra-docs.yml``.

When a pull request is submitted which changes the collection's documentation, a new docsite will be generated and published to a temporary site, and a bot will post a comment on the PR with a link. This will let you see the rendered docs to help with spotting formatting errors.

It's also possible to build the docs locally, by installing some extra Python requirements and running the build script:

.. code-block:: shell-session

    $ pushd docs/preview
    $ pip install -r requirements.txt
    $ ./build.sh

You can then find the generated HTML in ``docs/preview/build/html`` and can open them locally in your browser.

Running tests locally
=====================

If you're making anything more than very small or one-time changes, run the tests locally to avoid having to push a commit for each thing, and waiting for the CI to run tests.

First, :ref:`review the guidance on testing collections <testing_collections>`, as it applies to this collection as well.

Integration Tests
-----------------

Unlike other collections, we require an `integration_config.yml <https://docs.ansible.com/ansible/latest/dev_guide/testing_integration.html#integration-config-yml>`_ file for properly running integration tests, as the tests require external dependencies (like a Vault server) and they need to know where to find those dependencies.

If you have contributed to this collection or to the ``hashi_vault`` lookup plugin in the past, you might remember that the integration tests used to download, extract, and run a Vault server during the course of the tests, by default. This *legacy mode* is **no longer available**.


.. _ansible_collections.community.hashi_vault.docsite.contributor_guide.localenv_docker:

Docker Compose localenv
^^^^^^^^^^^^^^^^^^^^^^^

The recommended way to run the tests has Vault and other dependencies running in their own containers, set up via docker-compose, and the integration tests run in their own container separately.

We have a pre-defined "localenv" setup role for this purpose.

Usage
"""""

For ease of typing / length of commands, we'll enter the role directory first:

.. code-block:: shell-session

    $ pushd tests/integration/targets/setup_localenv_docker

This localenv has both Ansible collection and Python requirements, so let's get those out of the way:

.. code-block:: shell-session

    $ pip install -r files/requirements/requirements.txt -c files/requirements/constraints.txt
    $ ansible-galaxy collection install -r files/requirements/requirements.yml

To set up your docker-compose environment with all the defaults:

.. code-block:: shell-session

    $ ./setup.sh

The setup script does the following:

#. Template a ``docker-compose.yml`` for the project.
#. Generate a private key and self-signed certificate for Vault.
#. Template a Vault config file.
#. Bring down the existing compose project.
#. Bring up the compose project as defined by the vars (specified or defaults).
#. Template an ``integration_config.yml`` file that has all the right settings for integration tests to connect.
#. Copy the integration config to the correct location *if there isn't already one there* (it won't overwrite, in case you had customized changes).

With your containers running, you can now run the tests in docker (after returning back to the collection root):

.. code-block:: shell-session

    $ popd
    $ ansible-test integration --docker default --docker-network hashi_vault_default -v

The ``--docker-network`` part is important, because it ensures that the Ansible test container is in the same network as the dependency containers, that way the test container can reach them by their container names. The network name, ``hashi_vault_default`` comes from the default docker-compose project name used by this role (``hashi_vault``). See the :ref:`customization section <ansible_collections.community.hashi_vault.docsite.contributor_guide.localenv_docker_customization>` for more information.

Running ``setup.sh`` again can be used to re-deploy the containers, or if you prefer you can use the generated ``files/.output/<project_name>/docker-compose.yml`` directly with local tools.

If running again, remember to manually copy the contents of newly generated ``files/.output/integration_config.yml`` to the integration root, or delete the file in the root before re-running setup so that it copies the file automatically.

.. _ansible_collections.community.hashi_vault.docsite.contributor_guide.localenv_docker_customization:

Customization
"""""""""""""

``setup.sh`` passes any additional params you send it to the ``ansible-playbook`` command it calls, so you can customize variables with the standard ``--extra-vars`` (or ``-e``) option. There are many advanced scenarios possible, but a few things you might want to override:

* ``vault_version`` -- can target any version of Vault for which a docker container exists (this is the container's tag), defaults to ``latest``
* ``docker_compose`` (defaults to ``clean`` but could be set to ``up``, ``down``, or ``none``)
   * ``up`` -- similar to running ``docker-compose up`` (no op if the project is running as it should)
   * ``down`` -- similar to ``docker-compose down`` (destroys the project)
   * ``clean`` -- (default) similar to ``docker-compose down`` followed by ``docker-compose up``
   * ``none`` -- does the other tasks, including templating, but does not bring the project up or down. With this option, the ``community.docker`` collection is not required.
* ``vault_crypto_force`` -- by default this is ``false`` so if the cert and key exist they won't be regenerated. Setting to ``true`` will overwrite them.
* ``vault_port_http``, ``vault_port_https``, ``proxy_port`` -- all of the ports are exposed to the host, so if you already have any of the default ports in use on your host, you may need to override these.
* ``vault_container_name``, ``proxy_container_name`` -- these are the names for their respective containers, which will also be the DNS names used within the container network. In case you have the default names in use you may need to override these.
* ``docker_compose_project_name`` -- unlikely to need to be changed, but it affects the name of the docker network which will be needed for your ``ansible-test`` invocation, so it's worth mentioning. For example, if you set this to ``ansible_hashi_vault`` then the docker network name will be ``ansible_hashi_vault_default``.

.. _ansible_collections.community.hashi_vault.docsite.contributor_guide.contributing_auth_methods:

Contributing auth methods
=========================

In this collection, auth methods are shared among all plugins and modules rather than being re-implemented in each one. This saves the effort of re-inventing the wheel, prevents test bloat by having to test functionality across auth methods, and provides a consistent experience.

File location & scope
---------------------

Auth methods are implemented as classes in ``module_utils``, in a file named ``plugins/module_utils/_auth_method_<method_name>.py``. The leading underscore indicates that the module util is private to the collection and that it is not intended to be used outside the collection; this lets us make changes as needed without needing to release a new major version, and clearly indicates to would-be downstream users that they should not rely on these utils outside content within the collection.

In addition, all auth method module utils within the collection must contain a comment explaining this, such as:

.. code-block:: python

    # FOR INTERNAL COLLECTION USE ONLY
    # The interfaces in this file are meant for use within the community.hashi_vault collection
    # and may not remain stable to outside uses. Changes may be made in ANY release, even a bugfix release.
    # See also: https://github.com/ansible/community/issues/539#issuecomment-780839686
    # Please open an issue if you have questions about this.

It is best to look at `existing auth methods <https://github.com/ansible-collections/community.hashi_vault/tree/main/plugins/module_utils>`_ to get a feel for how they are implemented.

Class anatomy
-------------

Each auth method class should be named ``HashiVaultAuthMethod<MethodName>`` and inherit from ``HashiVaultAuthMethodBase``.

The base class provides some common functionality, like standardizing a way to emit warnings and providing a common function for validating required options.

An auth method must run the base class's ``__init__`` function.

It must implement two methods:

* ``validate()`` -- this method does everything it can to ensure that the requirements are met for performing authentication with this particular auth method. This may include checking for required options, validating the values of those options, pulling in additional information and context from the environment, preparing that information for use by ``authenticate()``, etc. Generally speaking, it should not contact Vault, and should minimize reliance on external sources and services, but that is a guideline and the details will depend on the specifics of the auth method in question. ``validate()`` raises an exception if validation fails. If it succeeds, nothing is returned.
* ``authenticate(client, use_token=False)`` -- this method performs the actual authentication, and it returns the API result of the authentication (which will include the token, lease information, etc.). The HVAC client object is passed in, as well an optional parameter ``use_token`` which specifies whether the client should have its token field set to the result of authentication (typically this is desired).

The auth method class should also contain two fields:

* ``NAME`` -- the name of the auth method.
* ``OPTIONS`` -- a list containing the name of every option that may be used by the auth method, including optional options; this list should not include the ``auth_method`` option.

Raising exceptions and warnings
-------------------------------

Because auth methods are shared among both Ansible modules and Ansible plugins, any exceptions raised must be applicable to both. Standard Python exceptions like ``KeyError`` can be raised if they appropriate.

In situations where you would normally raise ``AnsibleError`` (in plugins), or call ``module.fail_json()`` (in modules), you may raise ``HashiVaultValueError`` with your error message. Plugins and modules in this collection should expect this type and act accordingly.

Similarly for warnings, because plugins and modules implement warnings differently, module util code that needs to warn takes a warning callback, and this is true for auth methods as well.

The base class provides a ``warn()`` method that handles calling the callback specified at class init, so a simple ``self.warn()`` can be used in auth method code.

Accessing options
-----------------

Because auth methods are shared among both Ansible modules and Ansible plugins, which do not access options in the same way, this collection implements a class called ``HashiVaultOptionAdapter``. This class provides a standard interface for accessing option values in code that must work in both plugins and modules.

It implements the following methods:

* ``get_option(key)`` -- gets the option with the specified name. Raises ``KeyError`` if the option is not present.
* ``get_option_default(key, default=None)`` -- gets the option with the specified name. If it's not present, returns the value of ``default``.
* ``set_option(key, value)`` -- sets the value of the specified option ``key`` to ``value``.
* ``set_option_default(key, default=None)`` -- returns the value of the option ``key``. If the key is not present, sets its value to ``default`` and returns that value.
* ``has_option(key)`` -- returns ``True`` if the specified option *is present* (``None`` value counts as present).
* ``set_options(**kwargs)`` -- sets options to the key/value pairs specified in ``kwargs``.
* ``get_options(*args)`` -- returns a dict of the option names specified in ``args``.
* ``get_filtered_options(filter, *args)`` -- returns a dict of the option names specified in ``args``, if the callable ``filter`` (which has ``key`` and ``value`` passed into it) returns ``True`` for the given key/value pair.
* ``get_filled_options(*args)`` -- returns a dict of the option names specified in ``*args`` that are not ``None``.

The authenticator
-----------------

The ``HashiVaultAuthenticator`` class is how most of the content in the collection will handle authentication, rather than having to directly references each individual auth method. As a result, ``_authenticator.py`` needs to be modified for every new auth method, because it imports and directly references each class. See `the implementation of this class <https://github.com/ansible-collections/community.hashi_vault/blob/main/plugins/module_utils/_authenticator.py>`_ to find the places that need to be modified.

Auth method options and documentation
-------------------------------------

Because auth methods are shared among collection content, their options are documented in doc_fragment plugins. Because many options end up being shared among many auth methods (for example ``role_id``, ``username``, ``password``), we do not have a separate doc fragment for each auth method, as this would end up with duplicated option documentation.

Instead, all of the options for auth methods are in ``plugins/doc_fragments/auth.py``.

This contains the standard ``DOCUMENTATION`` field, as well as a ``PLUGINS`` field. The reason for this split is that there are certain parts of the documentation that are only applicable to plugins; namely the ``env``, ``ini``, and ``vars`` entries.

``DOCUMENTATION`` should contains all fields common to both, like ``description``, ``type``, ``version_added``, ``required``, etc., while anything plugin-specific goes in ``PLUGINS``.

Since plugins and modules will reference the doc fragments, it's not usually required to modify the docstrings in the content directly; if it seems necessary, please raise an issue to discuss.

Wherever possible, we should provide ``env``, ``ini``, and ``vars`` alternatives for specifying options, to give maximum flexibility for plugins. Occasionally, these won't make sense, like providing ``token`` (a sensitive value) in ``ini``.

When deciding to implement new options for an auth method, consider whether existing options can or should be reused. If a new option is needed, consider scoping its name to the auth method, in order to differentiate it from current or future option names that could be confusing in another context.

For example ``cert_auth_public_key`` and ``cert_auth_private_key`` were named that way to prevent them being confused with other certificate options that relate to the Vault connection, or other contexts where specific plugins or modules might need key pairs.

Testing auth methods
--------------------

Because auth methods are shared across the collection, we want them to be very well tested. Auth methods have both unit and integration tests, and the combination of those should give us high confidence that the methods work as intended.

Unit tests
^^^^^^^^^^

Unit tests allow us to check some of the functionality that is difficult to test effectively in integration tests, like checking that every possible combination of options behaves as it should, or simulating conditions that we can't easily reproduce. The coverage of various scenarios should be extensive, and the details of which, or how complex they are, will depend on the intricacies of the auth method itself. Looking at existing examples is highly recommended.

A pytest fixture is provided to load fixtures files that contain sample Vault API responses. Using these allows for mocking of the HVAC authentication calls within the unit tests.

Integration tests
^^^^^^^^^^^^^^^^^

Our integration tests provide a running Vault server, and with that we can set up any auth methods we want (in theory). In practice, auth methods often require external services to integrate with. When possible, we should consider setting up such external services so that we can create a meaningful, real life integration and test it.

Often however, this is not possible, or difficult. We must consider that tests are not only run in CI, but should be able to be run locally as well.

Mocking integrations
""""""""""""""""""""

We have implemented `MMock (Monster Mock) <https://github.com/jmartin82/mmock>`_ in our integration test setup to help with this. This server is setup to proxy its requests to the test Vault server, but you can write configurations that allow it to return different data for specific requests. By carefully constructing these responses, we can simulate the Vault API's response to login requests for specific auth methods, and also simulate its failures. With that, we can then run integration tests that hopefully provide us some assurance that we are implementing it correctly.

Testing plugin and module Usage
"""""""""""""""""""""""""""""""

Auth methods are usable from modules and plugins, so integration tests for an auth method must test it via both plugins and modules.

We provide custom modules and plugins specifically for testing auth methods within the integration tests. These are simplified implementations but they use the common code that should be used by all content, and they can be set to return some useful information about the login process. See the existing tests for details.

Test coverage
^^^^^^^^^^^^^

In CI, we use CodeCov to track coverage. We also set some specific "tags" in coverage, and one of those is to tag individual auth methods as targets for integration tests. This happens automatically in CI, however new auth methods need an entry into ``codecov.yml`` that maps the coverage flag to the file where the auth method is implemented. For example:

.. code:: yaml

    flags:
      target_auth_aws_iam:
        paths:
          - plugins/module_utils/_auth_method_aws_iam.py
