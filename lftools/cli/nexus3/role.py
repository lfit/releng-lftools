# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################

"""Nexus3 REST API role interface."""

__author__ = "DW Talton"

import logging
from pprint import pformat

import click
from tabulate import tabulate

log = logging.getLogger(__name__)


@click.group()
@click.pass_context
def role(ctx):
    """Role primary interface."""
    pass


@role.command(name="list")
@click.pass_context
def list_roles(ctx):
    """List roles."""
    r = ctx.obj["nexus3"]
    data = r.list_roles()
    log.info(tabulate(data, headers=["Roles"]))


@role.command(name="create")
@click.argument("name")
@click.argument("description")
@click.argument("privileges")
@click.argument("roles")
@click.pass_context
def create_role(ctx, name, description, privileges, roles):
    """Create roles."""
    r = ctx.obj["nexus3"]
    data = r.create_role(name, description, privileges, roles)
    log.info(pformat(data))
