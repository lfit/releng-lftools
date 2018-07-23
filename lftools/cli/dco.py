# SPDX-License-Identifier: MIT
##############################################################################
# Copyright (c) 2018 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Script to check a git repository for unsigned commits."""

__author__ = 'Jeremy Phelps'

import subprocess
import sys

import click


@click.group()
@click.pass_context
def dco(ctx):
    """Check repository for unsigned commits."""
    pass


@click.command()
@click.pass_context
def check(ctx, repository_url):
    """Check repository for unsigned commits.

    This check will exclude merge commits and empty commits

    """
    status = subprocess.call(['dco', 'check'])
    sys.exit(status)
