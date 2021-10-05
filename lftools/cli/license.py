# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Scan code for license headers."""

__author__ = "Thanh Ha"


import sys

import click

from lftools.license import check_license, check_license_directory


@click.group()
@click.pass_context
def license(ctx):
    """Scan code for license headers."""
    pass


@click.command()
@click.argument("source")
@click.option("-l", "--license", default="license-header.txt", help="License header file to compare against.")
@click.pass_context
def check(ctx, license, source):
    """Check files for missing license headers.

    Does not care if about line formatting of the license as long as all of the
    text is there and in the correct order.

    Note: This code only supports '#' comments for license headers.
    """
    exit_code = check_license(license, source)
    sys.exit(exit_code)


@click.command(name="check-dir")
@click.argument("directory")
@click.option("-l", "--license", default="license-header.txt", help="License header file to compare against.")
@click.option("-r", "--regex", default=r".+\.py$", help="File regex pattern to match on when searching.")
@click.pass_context
def check_directory(ctx, license, directory, regex):
    """Check directory for files missing license headers.

    Uses a regex pattern to find files to check for approved license headers.

    Does not care if about line formatting of the license as long as all of the
    text is there and in the correct order.

    Note: This code only supports '#' comments for license headers.
    """
    check_license_directory(license, directory, regex)


license.add_command(check)
license.add_command(check_directory)
