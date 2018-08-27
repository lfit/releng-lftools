# -*- coding: utf-8 -*-
# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Setup.py."""

from setuptools import find_packages
from setuptools import setup


with open('requirements.txt') as f:
    install_reqs = f.read().splitlines()

with open('requirements-test.txt') as f:
    f.readline()  # Skip the first -rrequirements.txt line
    test_reqs = f.read().splitlines()

setup(
    setup_requires=['pbr', 'pytest-runner'],
    pbr=True,
    install_requires=install_reqs,
    packages=find_packages(exclude=[
        '*.tests',
        '*.tests.*',
        'tests.*',
        'tests'
    ]),
    tests_require=test_reqs,
)
