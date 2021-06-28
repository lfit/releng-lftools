# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
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
    "fixtures",
)


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "schema"),
)
def test_check_license(cli_runner, datafiles):
    """Test check_schema() command."""
    os.chdir(str(datafiles))

    # Check that schema passes when schema and yaml are valid.
    result = cli_runner.invoke(cli.cli, ["schema", "verify", "release.yaml", "schema.yaml"], obj={})
    # noqa: B101 .
    assert result.exit_code == 0

    # Check that schema fails when schema and yaml are invalid.
    result = cli_runner.invoke(cli.cli, ["schema", "verify", "release-broken.yaml", "schema.yaml"], obj={})
    # noqa: B101 .
    assert result.exit_code == 1
