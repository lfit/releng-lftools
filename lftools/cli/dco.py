# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2018 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Script to check a git repository for commits missing DCO."""

__author__ = "DW Talton"

import sys

import click

from lftools.shell import dco as dco_checker


@click.group()
@click.pass_context
def dco(ctx):
    """Check repository for commits missing DCO."""
    pass


@click.command()
@click.argument("repo-path", required=False)
@click.pass_context
def check(ctx, repo_path):
    """Check repository for commits missing DCO.

    This check will exclude merge commits and empty commits.
    It operates in your current working directory which has to
    be a git repository.  Alternatively, you can opt to pass in the
    path to a git repo.
    Refer to https://developercertificate.org/
    """
    if not repo_path:
        repo_path = "."
    status = dco_checker.check(repo_path)
    sys.exit(status)


@click.command()
@click.argument("repo-path", required=False)
@click.pass_context
def match(ctx, repo_path):
    """Check for commits whose DCO does not match the commit author's email.

    This check will exclude merge commits and empty commits.
    It operates in your current working directory which has to
    be a git repository.  Alternatively, you can opt to pass in the
    path to a git repo.
    Refer to https://developercertificate.org/
    """
    if not repo_path:
        repo_path = "."
    status = dco_checker.match(repo_path)
    sys.exit(status)


dco.add_command(check)
dco.add_command(match)
