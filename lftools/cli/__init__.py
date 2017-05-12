# @License EPL-1.0 <http://spdx.org/licenses/EPL-1.0>
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
from lftools.cli.deploy import deploy
from lftools.cli.jenkins import jenkins_cli
from lftools.cli.nexus import nexus
from lftools.cli.version import version
from lftools.openstack.cmd import openstack


@click.group()
@click.pass_context
@click.version_option()
def cli(ctx):
    """CLI entry point for lftools."""
    pass


cli.add_command(deploy)
cli.add_command(openstack)
cli.add_command(nexus)
cli.add_command(jenkins_cli, name='jenkins')
cli.add_command(version)


def main():
    """Entry point for lftools CLI."""
    cli(obj={})


if __name__ == '__main__':
    main()
