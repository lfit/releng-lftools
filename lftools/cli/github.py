# @License EPL-1.0 <http://spdx.org/licenses/EPL-1.0>
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""CLI entry point for Github commands."""
import click
from lftools.github import cmd as githubcmd

__author__ = 'Jeremy Phelps'

@click.group()
@click.pass_context
def github(ctx):
    """Provide an interface to Github."""
    pass


@click.command()
@click.option('-c', '--config', type=str, required=True)
@click.pass_context
def create_webhook(ctx, config):
    githubcmd.create_webhooks(config)
