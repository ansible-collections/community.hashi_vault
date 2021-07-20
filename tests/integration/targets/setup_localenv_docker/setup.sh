#!/usr/bin/env bash

set -ex

pushd "${BASH_SOURCE%/*}"

ANSIBLE_ROLES_PATH="../" \
    ansible-playbook files/playbooks/vault_docker.yml "${@}"

# copy generated integration_config.yml if it doesn't exist
cp -n files/.output/integration_config.yml ../../ || true

popd
