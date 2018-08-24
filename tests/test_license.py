# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Test license command."""

import os

import pytest

from lftools import cli

FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'fixtures',
    )


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, 'license'),
    )
def test_check_license(cli_runner, datafiles):
    """Test check_license() command."""
    os.chdir(str(datafiles))

    # Check that license checker passes when file has license.
    result = cli_runner.invoke(cli.cli, ['license', 'check', 'license.py'], obj={})
    # noqa: B101 .
    assert result.exit_code == 0

    # Check that license checker fails when file is missing license.
    result = cli_runner.invoke(cli.cli, ['license', 'check', 'no_license1.py'], obj={})
    # noqa: B101 .
    assert result.exit_code == 1


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, 'license'),
    )
def test_check_license_directory(cli_runner, datafiles):
    """Test check_license_directory() command."""
    os.chdir(str(datafiles))

    # Check that check-dir fails due to directory containing files
    # with no license.
    result = cli_runner.invoke(cli.cli, ['license', 'check-dir', '.'], obj={})
    # noqa: B101 .
    assert result.exit_code == 1

    # Check that check-dir passes when directory contains files with licenses
    os.remove('no_license1.py')
    os.remove('no_license2.py')
    result = cli_runner.invoke(cli.cli, ['license', 'check-dir', '.'], obj={})
    # noqa: B101 .
    assert result.exit_code == 0
