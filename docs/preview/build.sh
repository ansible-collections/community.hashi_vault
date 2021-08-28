#!/usr/bin/env bash
set -e
pushd "${BASH_SOURCE%/*}"

# Create collection documentation into temporary directory
rm -rf temp-rst
mkdir -p temp-rst
antsibull-docs collection \
    --use-current \
    --dest-dir temp-rst \
    community.hashi_vault

# Copy collection documentation into source directory
rsync -avc --delete-after temp-rst/collections/ rst/collections/

# Build Sphinx site
sphinx-build -M html rst build -c . -W --keep-going

popd
