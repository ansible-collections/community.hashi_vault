#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: (c) 2021, Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import sys
import getopt

import json

import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from warnings import warn
from packaging import version


TAG_URI = 'https://registry.hub.docker.com/v2/repositories/%s/%s/tags?page_size=1024'


class WarningRetry(Retry):
    def new(self, **kwargs):
        if self.total > 0:
            warn('Error on request. Retries remaining: %i' % (self.total,))
        return super().new(**kwargs)


def main(argv):
    image = None
    include_prerelease = include_postrelease = False
    num_major_versions = 1
    num_minor_versions = 3
    num_micro_versions = 1

    opts, args = getopt.getopt(argv, '', [
        'image=',
        'num_major_versions=',
        'num_minor_versions=',
        'num_micro_versions=',
        'include_prerelease',
        'include_postrelease',
    ])

    for opt, arg in opts:
        if opt == '--image':
            image = image_name = arg
        elif opt == '--num_major_versions':
            num_major_versions = int(arg)
        elif opt == '--num_minor_versions':
            num_minor_versions = int(arg)
        elif opt == '--num_micro_versions':
            num_micro_versions = int(arg)
        elif opt == '--include_prerelease':
            include_prerelease = True
        elif opt == '--include_postrelease':
            include_postrelease = True

    if image is None:
        raise ValueError('image must be supplied.')

    if '/' in image:
        org, image_name = image.split('/')
    else:
        org = 'library'

    tag_url = TAG_URI % (org, image_name)

    sess = requests.Session()
    retry = WarningRetry(total=5, backoff_factor=0.2, respect_retry_after_header=False)
    adapter = HTTPAdapter(max_retries=retry)
    sess.mount('https://', adapter)

    response = sess.get(tag_url)

    versions = []
    for tag in response.json()['results']:
        vobj = None
        try:
            vobj = version.parse(tag['name'])
        except Exception:
            continue
        else:
            if not isinstance(vobj, version.Version):
                continue

        if vobj.is_prerelease is include_prerelease and vobj.is_postrelease is include_postrelease:
            versions.append(vobj)

    majors = set()
    minors = set()
    micros = set()
    keep = []
    for ver in sorted(versions, reverse=True):
        if ver.major not in majors:
            if len(majors) == num_major_versions:
                break
            majors.add(ver.major)
            minors.clear()
            micros.clear()

        if ver.minor not in minors:
            if len(minors) == num_minor_versions:
                continue
            minors.add(ver.minor)
            micros.clear()

        if ver.micro not in micros:
            if len(micros) == num_micro_versions:
                continue
            micros.add(ver.micro)

        keep.append(str(ver))

    with open(os.environ.get('GITHUB_OUTPUT', '/dev/stdout'), 'a') as f:
        f.write('versions=')
        json.dump(keep, f)


if __name__ == '__main__':
    main(sys.argv[1:])
