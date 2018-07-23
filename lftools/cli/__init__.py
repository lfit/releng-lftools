# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""CLI main for lftools."""

__author__ = 'Thanh Ha'

import click

from lftools.cli.config import config_sys
from lftools.cli.dco import dco
from lftools.cli.deploy import deploy
from lftools.cli.jenkins import jenkins_cli
from lftools.cli.license import license
from lftools.cli.nexus import nexus
from lftools.cli.sign import sign
from lftools.cli.version import version


@click.group()
@click.pass_context
@click.version_option()
def cli(ctx):
    """CLI entry point for lftools."""
    pass


cli.add_command(config_sys)
cli.add_command(deploy)
cli.add_command(dco)
cli.add_command(jenkins_cli, name='jenkins')
cli.add_command(license)
cli.add_command(nexus)
cli.add_command(sign)
cli.add_command(version)

try:
    from lftools.openstack.cmd import openstack
    cli.add_command(openstack)
except ImportError:
    from lftools.openstack.no_cmd import openstack
    cli.add_command(openstack)


def main():
    """Entry point for lftools CLI."""
    cli(obj={})


if __name__ == '__main__':
    main()
