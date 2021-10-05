# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################

"""Nexus3 REST API script interface."""

__author__ = "DW Talton"

import logging

import click

log = logging.getLogger(__name__)


@click.group()
@click.pass_context
def script(ctx):
    """Script primary interface."""
    pass


@script.command(name="create")
@click.argument("name")
@click.argument("filename")
@click.pass_context
def create_script(ctx, name, filename):
    """Create a new script."""
    r = ctx.obj["nexus3"]
    data = r.create_script(name, filename)
    log.info(data)


@script.command(name="delete")
@click.argument("name")
@click.pass_context
def delete_script(ctx, name):
    """Delete a script."""
    r = ctx.obj["nexus3"]
    data = r.delete_script(name)
    log.info(data)


@script.command(name="list")
@click.pass_context
def list_scripts(ctx):
    """List all scripts."""
    r = ctx.obj["nexus3"]
    data = r.list_scripts()
    log.info(data)


@script.command(name="read")
@click.argument("name")
@click.pass_context
def read_script(ctx, name):
    """Get script contents."""
    r = ctx.obj["nexus3"]
    data = r.read_script(name)
    log.info(data)


@script.command(name="run")
@click.argument("name")
@click.pass_context
def run_script(ctx, name):
    """Run a script."""
    r = ctx.obj["nexus3"]
    data = r.run_script(name)
    log.info(data)


@script.command(name="update")
@click.argument("name")
@click.argument("content")
@click.pass_context
def update_script(ctx, name, content):
    """Update script contents."""
    r = ctx.obj["nexus3"]
    data = r.update_script(name, content)
    log.info(data)
