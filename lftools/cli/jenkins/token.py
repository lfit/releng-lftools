# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2018 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Jenkins token commands."""

__author__ = 'Thanh Ha'

import logging

import click

from lftools.jenkins.token import get_token

log = logging.getLogger(__name__)


@click.group()
@click.pass_context
def token(ctx):
    """Get API token."""


@click.command()
@click.pass_context
def change(ctx):
    """Generate a new API token."""
    log.info(get_token(ctx.obj['jenkins_url'], True))


@click.command(name='print')
@click.pass_context
def print_token(ctx):
    """Print current API token."""
    log.info(get_token(ctx.obj['jenkins_url']))


token.add_command(change)
token.add_command(print_token)
