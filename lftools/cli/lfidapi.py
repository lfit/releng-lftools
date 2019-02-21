#!/usr/bin/env python2
# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2018 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Use the LFIDAPI to add, remove and list members as well as create groups."""

import subprocess
import sys

import click

from lftools.lfidapi import helper_add_remove_committers
from lftools.lfidapi import helper_create_group
from lftools.lfidapi import helper_invite
from lftools.lfidapi import helper_search_members
from lftools.lfidapi import helper_user


@click.group()
@click.pass_context
def lfidapi(ctx):
    """LFID API TOOLS."""
    pass


@click.command()
@click.argument('group')
@click.pass_context
def search_members(ctx, group):
    """List members of a group."""
    helper_search_members(group)


@click.command()
@click.argument('user')
@click.option('--delete', is_flag=True, required=False,
              help='remove user from group')
@click.argument('group')
@click.pass_context
def user(ctx, user, group, delete):
    """Add and remove users from groups."""
    helper_user(user, group, delete)


@click.command()
@click.argument('email')
@click.argument('group')
@click.pass_context
def invite(ctx, email, group):
    """Email invitation to join group."""
    helper_invite(email, group)


@click.command()
@click.argument('group')
@click.pass_context
def create_group(ctx, group):
    """Create group."""
    helper_create_group(group)


@click.command()
@click.argument('info_file')
@click.argument('ldap_file')
@click.argument('group')
@click.argument('user')
@click.pass_context
def add_remove_committers(ctx, info_file, ldap_file, group, user):
    """Used in automation."""
    helper_add_remove_committers(info_file, ldap_file, group, user)


@click.command()
@click.argument('git_dir')
@click.argument('gerrit_fqdn')
@click.argument('gerrit_project')
@click.pass_context
def lfidapi_add_remove_users(ctx, git_dir, gerrit_fqdn, gerrit_project):
    """Create a diff of the changes to the INFO.yaml.

    Call the api to add and remove users as appropriate.
    """
    status = subprocess.call(['lfidapi_add_remove_users', git_dir, gerrit_fqdn, gerrit_project])

    sys.exit(status)


lfidapi.add_command(search_members)
lfidapi.add_command(user)
lfidapi.add_command(invite)
lfidapi.add_command(create_group)
lfidapi.add_command(add_remove_committers)
lfidapi.add_command(lfidapi_add_remove_users)
