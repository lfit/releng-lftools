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

__author__ = 'DW Talton'

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
    log.info(
        tabulate(
            data,
            headers=[
                "ID",
                "Name",
                "Roles",
                "Privileges"
            ],
            tablefmt="grid"
        ))

