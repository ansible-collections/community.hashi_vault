#!/usr/bin/env bash

pushd "${BASH_SOURCE%/*}/files/playbooks"

ANSIBLE_ROLES_PATH="../../../" \
    ansible-playbook vault_docker.yml $@

popd
