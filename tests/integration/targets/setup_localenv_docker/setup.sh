#!/usr/bin/env bash

pushd "${BASH_SOURCE%/*}/files"

ANSIBLE_ROLES_PATH="../../" \
    ansible-playbook playbooks/vault_docker.yml "${@}"

popd
