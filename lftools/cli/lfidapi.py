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

import logging

import click

from lftools.lfidapi import (
    helper_create_group,
    helper_invite,
    helper_match_ldap_to_info,
    helper_search_members,
    helper_user,
)

log = logging.getLogger(__name__)


@click.group()
@click.pass_context
def lfidapi(ctx):
    """LFID API TOOLS."""
    pass


@click.command()
@click.argument("group")
@click.pass_context
def search_members(ctx, group):
    """List members of a group."""
    members = helper_search_members(group)
    for member in members:
        log.info("%s <%s>" % (member["username"], member["mail"]))


@click.command()
@click.argument("user")
@click.option("--delete", is_flag=True, required=False, help="remove user from group")
@click.argument("group")
@click.pass_context
def user(ctx, user, group, delete):
    """Add and remove users from groups."""
    helper_user(user, group, delete)


@click.command()
@click.argument("email")
@click.argument("group")
@click.pass_context
def invite(ctx, email, group):
    """Email invitation to join group."""
    helper_invite(email, group)


@click.command()
@click.argument("group")
@click.pass_context
def create_group(ctx, group):
    """Create group."""
    helper_create_group(group)


@click.command()
@click.argument("info_file")
@click.argument("group")
@click.option("--githuborg", type=str, required=False, help="github org name")
@click.option("--noop", is_flag=True, required=False, help="show what would be changed")
@click.pass_context
def match_ldap_to_info(ctx, info_file, group, githuborg, noop):
    """Match an LDAP or GITHUB group membership to an INFO.yaml file."""
    helper_match_ldap_to_info(info_file, group, githuborg, noop)


lfidapi.add_command(search_members)
lfidapi.add_command(user)
lfidapi.add_command(invite)
lfidapi.add_command(create_group)
lfidapi.add_command(match_ldap_to_info)
