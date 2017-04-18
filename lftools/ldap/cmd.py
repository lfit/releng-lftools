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
"""Library for creating identies and groups with LDAP."""

__author__ = 'Anil Belur'

import logging
import sys
import ldap
#import ldap.modlist as modlist
import yaml

import click
from lftools.ldap import odlldap as ldapcmd


@click.group()
@click.pass_context
def odl_ldap(ctx):
    """Provide an interface to OLD LDAP."""
    pass

@odl_ldap.group()
@click.pass_context
def odl_ldap(ctx):
    """Provide an interface to ODL ldap."""
    pass

@click.command()
@click.option(
    '-c', '--config', type=str, required=True,
    help='Project config file on project and memeber heirarchy.')
@click.option(
    '-s', '--settings', type=str, required=True,
    help='Config file containing ODL LDAP administrative settings.')
@click.pass_context
def create(ctx, config, settings):
    """Create LDAP groups and identies for ODL.

    This script creates a LDAP project group and adds initial committers
    to the group. LDAP server settings are read from settings.yaml and
    project creattion configuration is read from config.yaml
    """
    ldapcmd.create_ldap_groups_ids(config, settings)

odl_ldap.add_command(create)
