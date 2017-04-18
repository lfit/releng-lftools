# -*- code: utf-8 -*-
# @License EPL-1.0 <http://spdx.org/licenses/EPL-1.0>
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Library for creating LDAP identies and groups."""

__author__ = 'Anil Belur'


import click
from lftools.ldap import lfldap as ldapcmd


@click.group()
@click.pass_context
def ldap(ctx):
    """Provide an interface to ODL ldap."""
    pass


@click.command()
@click.option(
    '-c', '--config', type=str, required=True,
    help='Project config file on project and member heirarchy.')
@click.option(
    '-s', '--settings', type=str, required=True,
    help='Config file containing ODL LDAP administrative settings.')
@click.pass_context
def create(ctx, config, settings):
    """Create LDAP groups and identies for ODL."""
    ldapcmd.create_ldap_groups_ids(config, settings)


ldap.add_command(create)
