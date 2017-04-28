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
@click.option('-c', '--config', type=str, required=True,
              help="Path to config file for webhook settings.")
@click.option('-a', '--admin-config', type=str, required=True,
              help="Path to adminstrative config for Github auth.")
@click.option('-r', '--repository', type=str, required=True,
              help="Name of the Github repository.")
@click.pass_context
def create_webhooks(ctx, config, admin_config, repository):
    """Create a Github webhook."""
    githubcmd.create_webhooks(config, admin_config, repository)


github.add_command(create_webhooks)


@click.command()
@click.option('-c', '--config', type=str, required=True,
              help="Path to config file for branch protection settings.")
@click.option('-a', '--admin-config', type=str, required=True,
              help="Path to admistrative config for Github auth.")
@click.option('-r', '--repository', type=str, required=True,
              help="Name of the Github repository.")
@click.pass_context
def protect_branches(ctx, config, admin_config, repository):
    """Protect branches in a Github repository."""
    githubcmd.protect_branches(config, admin_config, repository)


github.add_command(protect_branches)


@click.command()
@click.option('-a', '--admin-config', type=str, required=True,
              help="Path to administrative config for Github auth.")
@click.option('-o', '--organization', type=str, required=True,
              help="Name of the Github organzation.")
@click.pass_context
def audit_org(ctx, config, admin_config):
    """Audit members of an organization, including the orgs teams."""
    pass


github.add_command(audit_org)
