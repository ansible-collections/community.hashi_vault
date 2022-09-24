#!/usr/bin/env bash
# Copyright (c) Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

set -e
pushd "${BASH_SOURCE%/*}"

# Create collection documentation into temporary directory
rm -rf temp-rst
mkdir -p temp-rst
antsibull-docs \
    --config-file antsibull-docs.cfg \
    collection \
    --use-current \
    --dest-dir temp-rst \
    community.hashi_vault

# Copy collection documentation into source directory
rsync -cprv --delete-after temp-rst/collections/ rst/collections/

# Build Sphinx site
sphinx-build -M html rst build -c . -W --keep-going

popd
