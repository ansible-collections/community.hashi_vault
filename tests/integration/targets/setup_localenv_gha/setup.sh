#!/usr/bin/env bash

set -eux

pushd "${BASH_SOURCE%/*}"

ANSIBLE_COLLECTIONS_PATHS="../../../../" \
ANSIBLE_ROLES_PATH="../" \
    ansible-playbook files/playbooks/gha.yml "${@}"

# launch containers
.output/launch.sh

# copy generated integration_config.yml if it doesn't exist
cp -n .output/integration_config.yml ../../ || true

popd
