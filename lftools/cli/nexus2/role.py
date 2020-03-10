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
def role(ctx):
    """User primary interface."""
    pass


@role.command(name="list")
@click.pass_context
def role_list(ctx):
    """List users."""
    r = ctx.obj["nexus2"]
    data = r.role_list()
    log.info(tabulate(data, headers=["ID", "Name", "Roles", "Privileges"], tablefmt="grid"))


@role.command(name="create")
@click.argument("role_id")
@click.argument("role_name")
@click.option("-d", "role_description", required=False)
@click.option("-r", "roles_list", required=False)
@click.option("-p", "privileges_list", required=False)
@click.pass_context
def role_create(ctx, role_id, role_name, role_description, roles_list, privileges_list):
    """Create a new role."""
    r = ctx.obj["nexus2"]
    data = r.role_create(role_id, role_name, role_description, roles_list, privileges_list)
    log.info(data)


@role.command(name="delete")
@click.argument("role_id")
@click.pass_context
def role_delete(ctx, role_id):
    """Delete a role."""
    r = ctx.obj["nexus2"]
    data = r.role_delete(role_id)
    log.info(data)
