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

Unlike other collections, we now require an `integration_config.yml <https://docs.ansible.com/ansible/latest/dev_guide/testing_integration.html#integration-config-yml>`_ file for properly running integration tests, as the tests require external dependencies (like a Vault server) and they need to know where to find those dependencies.

If you have contributed to this collection or to the ``hashi_vault`` lookup plugin in the past, you might remember that the integration tests used to download, extract, and run a Vault server during the course of the tests, by default. This **legacy mode** is not recommended but is still available (for now) via opt-in.

.. note::

  Legacy mode is not recommended because a new Vault server and proxy server will be downloaded, set up, configured, and/or uninstalled, for every *target*. Historically, we only had one target, and so it was a good way to go, but that's no longer true. This will make it slower and slower as more targets are added because you will incur the overhead on every target, in every run.

  Skip to :ref:`ansible_collections.community.hashi_vault.docsite.contributor_guide.localenv_docker` for a method that is nearly as easy as legacy mode, and far more efficient (docker-compose).

Legacy mode
^^^^^^^^^^^

To get started quickly without having to set anything else, you can use legacy mode by copying the included integration config sample:

.. code-block:: shell-session

    $ cp tests/integration/integration_config.yml.sample tests/integration/integration_config.yml

That file has everything configured to be able to run the integration tests and have them set up the dependencies for you.

.. warning::

  Legacy mode uses the GitHub API to figure out the latest version of HashiCorp Vault. This API has a `strict rate limit <https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting>`_ on anonymous requests and it's easy to hit that limit. You may set ``github_token`` within ``integration_config.yml`` to provide a token to use, which will give a much higher limit, however if you find yourself hitting the limit, it's probably easier to instead set ``vault_version`` to a specific version, which avoids the API call altogether.

You will also need the following additional Ansible collections:

* `community.crypto <https://galaxy.ansible.com/community/crypto>`_
* `community.general <https://galaxy.ansible.com/community/general>`_ (MacOS local/venv only)

Running legacy mode tests in docker (**recommended**):

.. code-block:: shell-session

    $ ansible-test integration --docker default -v

Running legacy mode tests in a controlled python virtual environment (**not recommended**):

.. code-block:: shell-session

    $ ansible-test integration --venv --requirements --allow-destructive -v

.. warning::

  In legacy mode, your system packages may be manipulated by running locally or in a venv (not in docker).

If you must use legacy mode testing, you can make it more efficient by limiting your test run to the specific target needed, to avoid the overhead of creating and destroying the dependencies for each target. For example:

.. code-block:: shell-session

    $ ansible-test integration --docker default -v lookup_hashi_vault

.. _ansible_collections.community.hashi_vault.docsite.contributor_guide.localenv_docker:

Docker Compose localenv
^^^^^^^^^^^^^^^^^^^^^^^

The recommended way to run the tests has Vault and tinyproxy running in their own containers, set up via docker-compose, and the integration tests run in their own container separately.

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
