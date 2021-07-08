#!/usr/bin/env bash

pushd "${BASH_SOURCE%/*}/files"

ANSIBLE_ROLES_PATH=../../ \
    ansible-playbook playbooks/gha.yml "${@}"

# launch containers
.output/launch.sh

# copy generated integration_config.yml if it doesn't exist
cp -n .output/integration_config.yml ../../../ || true

popd
