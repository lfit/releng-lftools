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
"""Unit tests for the version command."""

import filecmp
import os

import pytest

from lftools import cli

FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'fixtures',
    )


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, 'version_bump'),
    )
def test_version_bump(cli_runner, datafiles):
    """Test version bump command."""
    os.chdir(str(datafiles))
    cli_runner.invoke(cli.cli, ['version', 'bump', 'TestRelease'], obj={})

    for _file in datafiles.listdir():
        pom = str(_file) + '/pom.xml'
        expected_pom = str(_file) + '/pom.xml.expected'
        # noqa: B101 .
        assert filecmp.cmp(pom, expected_pom)


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, 'version_release'),
    )
def test_version_release(cli_runner, datafiles):
    """Test version release command."""
    os.chdir(str(datafiles))
    cli_runner.invoke(cli.cli, ['version', 'release', 'TestRelease'], obj={})

    for _file in datafiles.listdir():
        pom = str(_file) + '/pom.xml'
        expected_pom = str(_file) + '/pom.xml.expected'
        # noqa: B101 .
        assert filecmp.cmp(pom, expected_pom)
