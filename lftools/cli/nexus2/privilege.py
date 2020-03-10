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
def privilege(ctx):
    """User primary interface."""
    pass


@privilege.command(name="list")
@click.pass_context
def list(ctx):
    """List privileges."""
    r = ctx.obj["nexus2"]
    data = r.privilege_list()
    log.info(tabulate(data, headers=["Name", "ID"]))


@privilege.command(name="create")
@click.argument("name")
@click.argument("description")
@click.argument("repo")
@click.pass_context
def create(ctx, name, description, repo):
    """Create a new privilege."""
    r = ctx.obj["nexus2"]
    data = r.privilege_create(name, description, repo)
    log.info(data)


@privilege.command(name="delete")
@click.argument("privilege_id")
@click.pass_context
def delete(ctx, privilege_id):
    """Delete a privilege."""
    r = ctx.obj["nexus2"]
    data = r.privilege_delete(privilege_id)
    log.info(data)
