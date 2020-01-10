# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################

"""Nexus2 REST API repository interface."""

__author__ = 'DW Talton'

import logging
from pprint import pformat

import click
from tabulate import tabulate

log = logging.getLogger(__name__)


@click.group()
@click.pass_context
def repo(ctx):
    """Repository primary interface."""
    pass


@repo.command(name="list")
@click.pass_context
def repo_list(ctx):
    """List repositories."""
    r = ctx.obj["nexus2"]
    data = r.repo_list()
    log.info(
        tabulate(
            data,
            headers=[
                "Name",
                "Type",
                "Provider",
                "ID"
            ]
        ))
