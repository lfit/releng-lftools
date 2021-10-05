# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################

"""Nexus3 REST API user interface."""

__author__ = "DW Talton"

import logging

import click
from tabulate import tabulate

log = logging.getLogger(__name__)


@click.group()
@click.pass_context
def user(ctx):
    """User primary interface."""
    pass


@user.command(name="search")
@click.argument("username")
@click.pass_context
def search_user(ctx, username):
    """Search users."""
    r = ctx.obj["nexus3"]
    data = r.list_user(username)
    log.info(
        tabulate(
            data,
            headers=[
                "User ID",
                "First Name",
                "Last Name",
                "Email Address",
                "Status",
                "Roles",
            ],
        )
    )


@user.command(name="create")
@click.argument("username")
@click.argument("first_name")
@click.argument("last_name")
@click.argument("email_address")
@click.argument("roles")
@click.argument("password", required=False)
@click.pass_context
def user_create(ctx, username, first_name, last_name, email_address, roles, password):
    """Create a new user account."""
    r = ctx.obj["nexus3"]
    data = r.create_user(username, first_name, last_name, email_address, roles, password)
    log.info(data)


@user.command(name="delete")
@click.argument("username")
@click.pass_context
def user_delete(ctx, username):
    """Delete a user account."""
    r = ctx.obj["nexus3"]
    data = r.delete_user(username)
    log.info(data)
