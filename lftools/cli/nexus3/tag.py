# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################

"""Nexus3 REST API tag interface."""

import logging
from pprint import pformat

import click

log = logging.getLogger(__name__)


@click.group()
@click.pass_context
def tag(ctx):
    """Tag primary interface."""
    pass


@tag.command(name="add")
@click.argument("name")
@click.argument("attributes", required=False)
@click.pass_context
def add_tag(ctx, name, attributes):
    """Add a tag."""
    r = ctx.obj["nexus"]
    data = r.create_tag(name, attributes)
    log.info(pformat(data))


@tag.command(name="delete")
@click.argument("name")
@click.pass_context
def delete_tag(ctx, name):
    """Delete a tag."""
    r = ctx.obj["nexus"]
    data = r.delete_tag(name)
    log.info(pformat(data))


@tag.command(name="list")
@click.pass_context
def list_tags(ctx):
    """List tags."""
    r = ctx.obj["nexus"]
    data = r.list_tags()
    log.info(pformat(data))


@tag.command(name="show")
@click.argument("name")
@click.pass_context
def show_tag(ctx, name):
    """Show tags."""
    r = ctx.obj["nexus"]
    data = r.show_tag(name)
    log.info(pformat(data))
