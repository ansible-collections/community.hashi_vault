#!/usr/bin/env bash

pushd "${BASH_SOURCE%/*}/files"

ANSIBLE_ROLES_PATH=../../ \
    ansible-playbook playbooks/gha.yml "${@}"

.output/launch.sh

popd
