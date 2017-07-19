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

__author__ = 'Thanh Ha'


import click
from lftools.license import check_license


@click.group()
@click.pass_context
def license(ctx):
    """Scan code for license headers."""
    pass


@click.command()
@click.argument('source')
@click.option('-l', '--license', default='license-header.txt',
              help='License header file to compare against.')
@click.pass_context
def check(ctx, license, source):
    """Check files for missing license headers.

    Does not care if about line formatting of the license as long as all of the
    text is there and in the correct order.

    Note: This code only supports '#' comments for license headers.
    """
    check_license(license, source)


license.add_command(check)
