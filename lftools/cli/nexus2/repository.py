# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################

"""Nexus2 REST API repository interface."""

__author__ = "DW Talton"

import logging

import click
from tabulate import tabulate

log = logging.getLogger(__name__)


@click.group()
@click.pass_context
def repo(ctx):
    """Repository primary interface."""
    pass


@repo.command(name="list")
@click.pass_context
def repo_list(ctx):
    """List repositories."""
    r = ctx.obj["nexus2"]
    data = r.repo_list()
    log.info(tabulate(data, headers=["Name", "Type", "Provider", "ID"]))


@repo.command(name="create")
@click.argument("repo_type")
@click.argument("repo_id")
@click.argument("repo_name")
@click.argument("repo_provider")
@click.argument("repo_policy")
@click.option("-u", "--upstream-repo", "repo_upstream_url")
@click.pass_context
def create(ctx, repo_type, repo_id, repo_name, repo_provider, repo_policy, repo_upstream_url):
    """Create a new repository."""
    r = ctx.obj["nexus2"]
    data = r.repo_create(repo_type, repo_id, repo_name, repo_provider, repo_policy, repo_upstream_url)
    log.info(data)


@repo.command(name="delete")
@click.argument("repo_id")
@click.pass_context
def delete(ctx, repo_id):
    """Permanently delete a repo."""
    r = ctx.obj["nexus2"]
    data = r.repo_delete(repo_id)
    log.info(data)
