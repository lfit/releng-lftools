# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################

"""Nexus2 REST API user interface."""

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


@user.command(name="list")
@click.pass_context
def user_list(ctx):
    """List users."""
    r = ctx.obj["nexus2"]
    data = r.user_list()
    log.info(tabulate(data, headers=["ID", "First Name", "Last Name", "Status", "Roles"]))


@user.command(name="add")
@click.argument("username")
@click.argument("firstname")
@click.argument("lastname")
@click.argument("email")
@click.argument("roles")
@click.argument("password", required=False)
@click.pass_context
def user_create(ctx, username, firstname, lastname, email, roles, password):
    """Add a new user."""
    r = ctx.obj["nexus2"]
    data = r.user_create(username, firstname, lastname, email, roles, password)
    log.info(data)


@user.command(name="delete")
@click.argument("username")
@click.pass_context
def user_details(ctx, username):
    """Delete a user."""
    r = ctx.obj["nexus2"]
    data = r.user_delete(username)
    log.info(data)
