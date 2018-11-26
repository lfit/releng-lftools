# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2018 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Create a gerrit project."""

from __future__ import print_function

import subprocess
import sys

import click


@click.group()
@click.pass_context
def gerrit_cli(ctx):
    """GERRIT TOOLS."""
    pass


@click.command()
@click.argument('user')
@click.argument('gerrit_url')
@click.argument('repo')
@click.pass_context
def create(ctx, user, gerrit_url, repo):
    """Create a gerrit repo."""
    status = subprocess.call(['gerrit_create', user, gerrit_url, repo])
    sys.exit(status)


gerrit_cli.add_command(create)
