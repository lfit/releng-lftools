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
    pass

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
    pass

@click.command()
@click.option('-a', '--admin-config', type=str, required=True,
              help="Path to administrative config for Github auth.")
@click.option('-o', '--organization', type=str, required=True,
              help="Name of the Github organzation.")
@click.pass_context
def list_org_members(ctx, organization, admin_config):
    """Audit members of an organization"""
    githubcmd.get_org_members(organization, admin_config)

@click.command()
@click.option('-a', '--admin-config', type=str, required=True,
              help="Path to administrative config for Github auth.")
@click.option('-o', '--organization', type=str, required=True,
              help="Name of the Github organzation.")
@click.pass_context
def list_org_repos(ctx, organization, admin_config):
    """Audit repositories of an organization"""
    githubcmd.get_org_repos(organization, admin_config)

@click.command()
@click.option('-a', '--admin-config', type=str, required=True,
              help="Path to administrative config for Github auth.")
@click.option('-o', '--organization', type=str, required=True,
              help="Name of the Github organzation.")
@click.pass_context
def list_org_teams(ctx, organization, admin_config):
    """Audit teams of an organization"""
    githubcmd.get_org_teams(organization, admin_config)

@click.command()
@click.option('-a', '--admin-config', type=str, required=True,
              help="Path to administrative config for Github auth.")
@click.option('-t', '--team_id', type=str, required=True,
              help="Name of the Github organzation.")
@click.pass_context
def list_team_members(ctx, team_id, admin_config):
    """Audit members of a team"""
    githubcmd.get_team_members(team_id, admin_config)

@click.command()
@click.option('-a', '--admin-config', type=str, required=True,
              help="Path to administrative config for Github auth.")
@click.option('-o', '--organization', type=str, required=True,
              help="Name of the Github organzation.")
@click.pass_context
def org_team_member_audit(ctx, organization, admin_config):
    """Audit teams of an organization"""
    githubcmd.org_team_member_audit(organization, admin_config)

@click.command()
@click.option('-a', '--admin-config', type=str, required=True,
              help="Path to administrative config for Github auth.")
@click.option('-o', '--organization', type=str, required=True,
              help="Name of the Github organzation.")
@click.option('-r', '--repository', type=str, required=True,
              help="Name of the repository.")
@click.pass_context
def list_repo_collaborators(ctx, organization, repository, admin_config):
    """Audit repositories of an organization"""
    githubcmd.get_repo_collaborators(organization, repository, admin_config)

@click.command()
@click.option('-a', '--admin-config', type=str, required=True,
              help="Path to administrative config for Github auth.")
@click.option('-p', '--owner', type=str, required=True,
              help="Name of the Github organzation.")
@click.option('-r', '--repository', type=str, required=True,
              help="Name of the repository.")
@click.pass_context
def list_repo_contributors(ctx, owner, repository, admin_config):
    """Audit contributors of an organization"""
    githubcmd.get_repo_contributors(owner, repository, admin_config)

@click.command()
@click.option('-a', '--admin-config', type=str, required=True,
              help="Path to administrative config for Github auth.")
@click.pass_context
def get_rate_limit_status(ctx, admin_config):
    """Query API rate limit stats"""
    githubcmd.get_rate_limit_status(admin_config)


github.add_command(get_rate_limit_status)
github.add_command(list_repo_collaborators)
github.add_command(list_repo_contributors)
github.add_command(list_org_members)
github.add_command(list_org_repos)
github.add_command(list_org_teams)
github.add_command(org_team_member_audit)
github.add_command(protect_branches)
github.add_command(create_webhooks)
