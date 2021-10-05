# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################

"""Nexus3 REST API repository interface."""

__author__ = "DW Talton"

import logging
from pprint import pformat

import click

log = logging.getLogger(__name__)


@click.group()
@click.pass_context
def repository(ctx):
    """Repository primary interface."""
    pass


@repository.command(name="list")
@click.pass_context
def list_repositories(ctx):
    """List repositories."""
    r = ctx.obj["nexus3"]
    data = r.list_repositories()
    log.info(pformat(data))
