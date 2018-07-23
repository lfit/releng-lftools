# SPDX-License-Identifier: MIT
##############################################################################
# Copyright (c) 2018 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Script to check a git repository for commits missing DCO.
   Refer to https://developercertificate.org/
"""

import subprocess
import sys

import click


@click.group()
@click.pass_context
def dco(ctx):
    """Check repository for commits missing DCO."""
    pass

@click.command()
@click.pass_context
def check(ctx):
    """Check repository for commits missing DCO.

    This check will exclude merge commits and empty commits
    Refer to https://developercertificate.org/
    """
    status = subprocess.call(['dco_check'])
    sys.exit(status)
