# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################

"""Nexus3 REST API privileges interface."""

__author__ = "DW Talton"

import logging

import click
from tabulate import tabulate

log = logging.getLogger(__name__)


@click.group()
@click.pass_context
def privilege(ctx):
    """Privilege primary interface."""
    pass


@privilege.command(name="list")
@click.pass_context
def list_privileges(ctx):
    """List privileges."""
    r = ctx.obj["nexus3"]
    data = r.list_privileges()
    log.info(tabulate(data, headers=["Type", "Name", "Description", "Read Only"]))
