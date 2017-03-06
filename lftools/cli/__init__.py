# @License EPL-1.0 <http://spdx.org/licenses/EPL-1.0>
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# Contributors:
#   Thanh Ha - Initial implementation
##############################################################################
"""CLI main for lftools."""
import click
from lftools.cli.version import version


@click.group()
@click.pass_context
@click.version_option()
def cli(ctx):
    """CLI entry point for lftools."""
    pass


cli.add_command(version)


if __name__ == '__main__':
    cli(obj={})
