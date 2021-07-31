# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################

"""Nexus3 REST API asset interface."""

__author__ = "DW Talton"

import logging
from pprint import pformat

import click

log = logging.getLogger(__name__)


@click.group()
@click.pass_context
def asset(ctx):
    """Asset primary interface."""
    pass


@asset.command(name="list")
@click.argument("repository")
@click.pass_context
def asset_list(ctx, repository):
    """List assets."""
    r = ctx.obj["nexus3"]
    data = r.list_assets(repository)
    for item in data:
        log.info(pformat(item))


@asset.command(name="search")
@click.argument("query-string")
@click.argument("repository")
@click.option("--details", is_flag=True)
@click.pass_context
def asset_search(ctx, query_string, repository, details):
    """Search assets."""
    r = ctx.obj["nexus3"]
    data = r.search_asset(query_string, repository, details)

    if details:
        log.info(data)
    else:
        for item in data:
            log.info(item)
