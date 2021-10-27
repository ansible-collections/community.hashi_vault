.. _ansible_collections.community.hashi_vault.docsite.user_guide:

**********
User guide
**********

The `community.hashi_vault collection <https://galaxy.ansible.com/community/hashi_vault>`_ offers Ansible content for working with `HashiCorp Vault <https://www.vaultproject.io/>`_.

.. note::

  This guide is a work-in-progress and should not be considered complete. Use it in conjunction with plugin documentation.

.. contents::
  :local:
  :depth: 1


.. _ansible_collections.community.hashi_vault.docsite.user_guide.requirements:

Requirements
============

The content in ``community.hashi_vault`` requires the `hvac <https://hvac.readthedocs.io/en/stable/>`_ library.

.. code-block:: shell-session

    $ pip install hvac

``hvac`` version specifics
--------------------------

In general, we recommend using the latest version of ``hvac`` that is supported for your given Python version because that is what we test against. Where possible we will try to list version-specific restrictions here, but this list may not be exhaustive.

* ``hvac`` 0.7.0+ (for namespace support)
* ``hvac`` 0.9.6+ (to avoid most deprecation warnings)
* ``hvac`` 0.10.5+ (for JWT auth)
* ``hvac`` 0.10.6+ (to avoid deprecation warning for AppRole)
* ``hvac`` 0.10.12+ (for cert auth)

Other requirements
------------------

* ``boto3`` (only if loading credentials from a boto session, for example using an AWS profile or IAM role credentials)

Retrying failed requests
========================

Via the ``retries`` parameter, you can control what happens when a request to Vault fails, and automatically retry certain requests. Retries are based on the `urllib3 Retry class <https://urllib3.readthedocs.io/en/latest/reference/urllib3.util.html#urllib3.util.Retry>`_ and so all of its options are supported.

Retries are disabled by default.

In ``community.hashi_vault`` you can specify the ``retries`` parameter in two ways:

* Set a positive number (integer), where ``0`` disables retries and any positive number sets the number of tries, with the rest of the retry parameters using the collection defaults.
* Set a dictionary, where you can set any field that the ``Retry`` class can be initialized with, in order to fully customize your retry experience.


About the collection defaults
-----------------------------

The collection uses its own set of recommended defaults for retries, including which HTTP status codes to retry, which HTTP methods are subject to retries, and the backoff factor used. **These defaults are subject to change at any time (in any release) and won't be considered breaking changes.** By setting ``retries`` to a number you are opting in to trust the defaults in the collection. To enable retries with full control over its behavior, be sure to specify a dictionary.

Current Defaults (always check the source code to confirm the defaults in your specific collection version):

.. code-block:: yaml

    status_forcelist:
      # https://www.vaultproject.io/api#http-status-codes
      # 429 is usually a "too many requests" status, but in Vault it's the default health status response for standby nodes.
      - 500 # Internal server error. An internal error has occurred, try again later. If the error persists, report a bug.
      - 502 # A request to Vault required Vault making a request to a third party; the third party responded with an error of some kind.
      - 503 # Vault is down for maintenance or is currently sealed. Try again later.
    allowed_methods: null # None allows retries on all methods, including those which may not be considered idempotent, like POST
    backoff_factor: 0.3

Any of the ``Retry`` class's parameters that are not specified in the collection defaults or in your custom dictionary, are initialized using the class's defaults, with one exception: the ``raise_on_status`` parameter is always set to ``false`` unless you explicitly added it your custom dictionary. The reason is that this lets our error handling look for the expected ``hvac`` exceptions, instead of the ``Retry``-specfic exceptions. It is recommended that you don't override this as it may cause unexpected error messages on common failures if they are retried.

Controlling retry warnings
--------------------------

By default, if a retry is performed, a warning will be emitted that shows how many retries are remaining. This can be controlled with the ``retry_action`` option which defaults to ``warn``. It is recommended to keep this enabled unless you have other processes that will be thrown off by the warning output.

A note about timeouts
---------------------

Consider setting the ``timeout`` option appropriately when using retries, as a connection timeout doesn't count toward time between retries (backoff). A long timeout can cause very long delays for a connection that isn't going to recover, multiplied by number of retries.

However, also consider the type of request being made, and the auth method in use. Because Vault auth methods may have their own dependencies on other systems (an LDAP server, a cloud provider like AWS, a required MFA prompt that depends on a human to respond), the time to complete a request could be quite long, and setting a timeout too short will prevent an otherwise successful request from completing.
