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

from lftools import __summary__
from lftools import __version__

with open('requirements.txt') as f:
    install_reqs = f.read().splitlines()

with open('requirements-openstack.txt') as f:
    openstack_reqs = f.read().splitlines()

setup(
    name='lftools',
    version=__version__,
    author='Thanh Ha',
    author_email='releng@linuxfoundation.org',
    url='https://lf-releng-tools.readthedocs.io',
    description=__summary__,
    long_description=open("README.md").read(),
    license='EPL',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
    ],
    install_requires=install_reqs,
    extras_require={
        'openstack': openstack_reqs,
    },
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
        'shell/dco',
        'shell/deploy',
        'shell/sign',
        'shell/version'
    ],
    data_files=[('etc', ['etc/logging.ini'])],
)
