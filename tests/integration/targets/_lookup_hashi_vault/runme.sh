#!/usr/bin/env bash

set -eux

export ANSIBLE_TEST_PREFER_VENV=1  # see https://github.com/ansible/ansible/pull/73000#issuecomment-757012395; can be removed once Ansible 2.9 and ansible-base 2.10 support has been dropped
source virtualenv.sh

# (thanks https://github.com/ansible-collections/servicenow.itsm/blob/main/tests/integration/targets/inventory/runme.sh)
# When running script-based integration targets, `ansible-test integration`
# does not make these variables available. We will need to pass them
# explicitly, as extra vars to `ansible-playbook` command.
readonly vars_file=../../integration_config.yml

if [[ ! -f "$vars_file" ]]; then
    # cp -T "${vabs}.template" "$vabs"
    echo -e "---\ndummy: 0" > "$vars_file"
fi

# First install pyOpenSSL, then test lookup in a second playbook in order to
# workaround this error which occurs on OS X 10.11 only:
#
# TASK [lookup_hashi_vault : test token auth with certs (validation enabled, lookup parameters)] ***
# included: lookup_hashi_vault/tasks/token_test.yml for testhost
#
#   TASK [lookup_hashi_vault : Fetch secrets using "hashi_vault" lookup] ***
#   From cffi callback <function _verify_callback at 0x106f995f0>:
#   Traceback (most recent call last):
#     File "/usr/local/lib/python2.7/site-packages/OpenSSL/SSL.py", line 309, in wrapper
#       _lib.X509_up_ref(x509)
#   AttributeError: 'module' object has no attribute 'X509_up_ref'
#   fatal: [testhost]: FAILED! => { "msg": "An unhandled exception occurred while running the lookup plugin 'hashi_vault'. Error was a <class 'requests.exceptions.SSLError'>, original message: HTTPSConnectionPool(host='localhost', port=8201): Max retries exceeded with url: /v1/auth/token/lookup-self (Caused by SSLError(SSLError(\"bad handshake: Error([('SSL routines', 'ssl3_get_server_certificate', 'certificate verify failed')],)\",),))"}

ANSIBLE_ROLES_PATH=../ \
    ansible-playbook playbooks/install_dependencies.yml -e "@$vars_file" -v "$@"

ANSIBLE_ROLES_PATH=../ \
    ansible-playbook playbooks/test_lookup_hashi_vault.yml -e "@$vars_file" -v "$@"
