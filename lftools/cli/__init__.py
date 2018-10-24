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

import getpass
import logging

import click
from six.moves import configparser
from six.moves import input

from lftools import config as conf
from lftools.cli.config import config_sys
from lftools.cli.dco import dco
from lftools.cli.deploy import deploy
from lftools.cli.infofile import infofile
from lftools.cli.jenkins import jenkins_cli
from lftools.cli.license import license
from lftools.cli.nexus import nexus
from lftools.cli.sign import sign
from lftools.cli.version import version

log = logging.getLogger(__name__)


@click.group()
@click.option('--debug', envvar='DEBUG', is_flag=True, default=False)
@click.option('--password', envvar='LFTOOLS_PASSWORD', default=None)
@click.option('--username', envvar='LFTOOLS_USERNAME', default=None)
@click.option('-i', '--interactive', is_flag=True, default=False)
@click.pass_context
@click.version_option()
def cli(ctx, debug, interactive, password, username):
    """CLI entry point for lftools."""
    if debug:
        logging.getLogger("").setLevel(logging.DEBUG)

    ctx.obj['DEBUG'] = debug
    log.debug('DEBUG mode enabled.')

    # Start > Credentials
    if username is None:
        if interactive:
            username = input('Username: ')
        else:
            try:
                username = conf.get_setting('global', 'username')
            except (configparser.NoOptionError,
                    configparser.NoSectionError) as e:
                username = None

    if password is None:
        if interactive:
            password = getpass.getpass('Password: ')
        else:
            try:
                password = conf.get_setting('global', 'password')
            except (configparser.NoOptionError,
                    configparser.NoSectionError) as e:
                password = None

    ctx.obj['username'] = username
    ctx.obj['password'] = password
    # End > Credentials


cli.add_command(config_sys)
cli.add_command(infofile)
cli.add_command(deploy)
cli.add_command(dco)
cli.add_command(jenkins_cli, name='jenkins')
cli.add_command(license)
cli.add_command(nexus)
cli.add_command(sign)
cli.add_command(version)

try:
    from lftools.cli.ldap_cli import ldap_cli
    cli.add_command(ldap_cli, name='ldap')
except ImportError:
    from lftools.cli.no_cmd import no_ldap as ldap_cli
    cli.add_command(ldap_cli, name='ldap')


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
