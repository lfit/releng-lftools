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

from lftools import __version__

desc = '''Linux Foundation Release Engineering Tools
Website: https://lf-releng-tools.readthedocs.io/en/latest/
'''

long_desc = '''
LF Tools is a collection of scripts and utilities that are useful to multiple
Linux Foundation project CI and Releng related activities. We try to create
these tools to be as generic as possible such that they can be deployed in
other environments.

Ubuntu Dependencies:

    - build-essentials
    - python-dev
'''

with open('requirements.txt') as f:
    install_reqs = f.read().splitlines()

setup(
    name='lftools',
    version=__version__,
    author='Thanh Ha',
    author_email='thanh.ha@linuxfoundation.org',
    url='',
    description=(desc),
    long_description=long_desc,
    license='EPL',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
    ],
    install_requires=install_reqs,
    packages=find_packages(exclude=[
        '*.tests',
        '*.tests.*',
        'tests.*',
        'tests'
    ]),
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    entry_points='''
        [console_scripts]
        lftools=lftools.cli:main
    ''',
    scripts=[
        'shell/deploy',
        'shell/sign',
        'shell/version',
    ],
    data_files=[('etc', ['etc/logging.ini'])],
)
