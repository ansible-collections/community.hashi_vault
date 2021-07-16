.. _ansible_collections.community.hashi_vault.docsite.contributor_guide:

Contributor Guide
=================

This guide aims to help PR authors contribute to the ``community.hashi_vault`` collection.

**NOTE:** this guide is a work-in-progress and should not be considered complete. Check back often as we fill out more details based on experience and feedback, and please let us know how this guide can be improved.


.. contents::
  :local:
  :depth: 3


Quick Start
-----------

#. Log into your GitHub account.
#. Fork the `ansible-collections/community.hashi_vault repository <https://github.com/ansible-collections/community.hashi_vault>`_ by clicking the **Fork** button in the upper right corner. This will create a fork in your own account.
#. Clone the repository locally, following `the example instructions here <https://docs.ansible.com/ansible/devel/dev_guide/developing_collections_contributing.html>`_ (but replace ``general`` with ``hashi_vault``). **Pay special attention to the path structure.**
#. As mentioned on that page, commit your changes to a branch, push them to your fork, and create a pull request (GitHub will automatically prompt you to do so when you look at your repository).
#. `See the guidance on Changelogs <https://docs.ansible.com/ansible/latest/community/development_process.html#changelogs>`_ and include a `changelog fragment <https://docs.ansible.com/ansible/latest/community/development_process.html#creating-a-changelog-fragment>`_ if appropriate.


Running Tests Locally
---------------------

If you're making anything more than very small or one-time changes, you'll want to run the tests locally to avoid having to push a commit for each thing, and waiting for the CI to run tests.

First, `review the guidance on testing collections <https://docs.ansible.com/ansible/devel/dev_guide/developing_collections_testing.html#testing-collections>`_, as it applies to this collection as well.

Integration Tests
-----------------

Unlike other collections, we now require an `integration_config.yml <https://docs.ansible.com/ansible/latest/dev_guide/testing_integration.html#integration-config-yml>`_ file for properly running integration tests, as the tests require external dependencies (like a Vault server) and they need to know where to find those dependencies.

If you have contributed to this collection or to the ``hashi_vault`` lookup plugin in the past, you might remember that the integration tests used to download, extract, and run a Vault server during the course of the tests, by default. This **legacy method** is not recommended but is still available (for now) via opt-in.

Skip to the next section for a method that's nearly as easy but better off in the long run (docker-compose).

Legacy Mode
...........

To get started quickly without having to set anything else, you can use legacy mode by copying the included integration config sample:

.. code-block:: bash

    $ cp tests/integration/integration_config.yml.sample tests/integration/integration_config.yml

That file has everything configured to be able to run the integration tests and have them set up the dependencies for you.

You will also need the following additional Ansible collections:

* `community.crypto <https://galaxy.ansible.com/community/crypto>`_
* `community.general <https://galaxy.ansible.com/community/general>`_ (MacOS local/venv only)

Running legacy mode tests in docker (recommended):

.. code-block:: bash

    $ ansible-test integration --docker default -v

Running legacy mode tests in a controlled python virtual environment (**not recommended**):

.. code-block:: bash

    $ ansible-test integration --venv --requirements --allow-destructive -v

Note that your system packages may be manipulated by running locally or in a venv.

Legacy mode is not recommended because a new Vault server and proxy server will be downloaded, set up, configured, and/or uninstalled, for every *target*. Traditionally, we've only had one target, and so it was a good way to go, but that's no longer going to be the case. This is going to make it slower and slower as you'll incur the overhead on every target, in every run.

If you must use legacy mode testing, you can make it more efficient by limiting your test run to the specific target needed, for example:

.. code-block:: bash

    $ ansible-test integration --docker default -v lookup_hashi_vault

Docker Compose localenv
.......................

The recommended way to run the tests has Vault and tinyproxy running in their own containers, set up via docker-compose, and the integration tests run in their own container separately.

We have a pre-defined "localenv" setup role for this purpose.

Usage
~~~~~

For ease of typing / length of commands, we'll enter role directory first:

.. code-block:: bash

    $ pushd tests/integration/targets/setup_localenv_docker

This localenv has both Ansible collection and Python requirements, so let's get those out of the way:

.. code-block:: bash

    $ pip install -r files/requirements/requirements.txt -c files/requirements/constraints.txt
    $ ansible-galaxy collection install -r files/requirements/requirements.yml

To set up your docker-compose environment with the all defaults:

.. code-block:: bash

    $ ./setup.sh

This will do the following:

#. Template a ``docker-compose.yml`` for the project.
#. Generate a private key and self-signed certificate for Vault.
#. Template a Vault config file.
#. Bring down the existing compose project.
#. Bring up the compose project as defined by the vars (specified or defaults).
#. Template an ``integration_config.yml`` file that has all the right info for integration tests to connect.
#. Will copy the integration config to the correct location *if there isn't already one there* (it won't overwrite, in case you had customized changes).

With your containers running, you can now run the tests in docker (after returning back to the collection root):

.. code-block:: bash

    $ popd
    $ ansible-test integration --docker default --docker-network hashi_vault_default -v

The ``--docker-network`` part is important, as it will ensure that the Ansible test container is in the same network as the dependency containers, that way the test container can reach them by their container names. The network name, ``hashi_vault_default`` comes from the default docker-compose project name used by this role (``hashi_vault``). See the next section for more information.

Running ``setup.sh`` again can be used to re-deploy the containers, or if you prefer you can use the generated ``docker-compose.yml`` in ``files/.output/<project_name>``.

If running again, remember to manually copy the contents of newly generated ``files/.output/integration_config.yml`` to the integration root, or delete the file in the root before re-running setup so that it copies the file automatically.

Customization
~~~~~~~~~~~~~

``setup.sh`` will pass any additional params you send it to the ``ansible-playbook`` command it calls, so you can customize variables with the standard ``-e`` option. There are many advanced scenarios possible, but a few things you might want to override:

* ``vault_version`` -- can target any version of Vault for which a docker container exists
* ``docker_compose`` (defaults to ``clean`` but could be set to ``up``, ``down``, or ``none``)
  * ``up`` -- similar to running ``docker-compose up`` (no op if the project is running as it should)
  * ``down`` -- similar to ``docker-compose down`` (destroys the project)
  * ``clean`` -- (default) similar to ``docker-compose down`` followed by ``docker-compose up``
  * ``none`` -- does the other tasks, including templating, but does not bring the project up or down. With this option, the ``community.docker`` collection is not required.
* ``vault_crypto_force`` -- by default this is ``false`` so if the cert and key exist they won't be regenerated. Setting to ``true`` will overwrite them.
* ``vault_port_http``, ``vault_port_https``, ``proxy_port`` -- all of the ports are exposed to the host, so if you already have any of the default ports in use on your host, you may need to override these.
* ``vault_container_name``, ``proxy_container_name`` -- these are the names for their respective containers, which will also be the DNS names used within the container network. In case you have the default names in use you may need to override these.
* ``docker_compose_project_name`` -- unlikely to need to be changed, but it affects the name of the docker network which will be needed for your ``ansible-test`` invocation, so it's worth mentioning. For example, if you set this to ``ansible_hashi_vault`` then the docker network name will be ``ansible_hashi_vault_default``.
