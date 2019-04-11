# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Github tools."""

from __future__ import print_function

import sys

import click
from github import Github
from github import GithubException

from lftools import config


@click.group()
@click.pass_context
def github_cli(ctx):
    """GITHUB TOOLS."""
    pass


@click.command(name='list')
@click.argument('organization')
@click.pass_context
def list(ctx, organization):
    """List and Organizations GitHub repos."""
    token = config.get_setting("github", "token")
    g = Github(token)
    orgName = organization
    print("All repos for organization: ", orgName)
    try:
        org = g.get_organization(orgName)
    except GithubException as ghe:
        print(ghe)
    repos = org.get_repos()
    for repo in repos:
        print(repo.name)

@click.command(name='audit')
@click.argument('organization')
@click.pass_context
def audit(ctx, organization):
    """List Users for an Org that do not have 2fa enabled."""
    token = config.get_setting("github", "token")
    g = Github(token)
    orgName = organization
    try:
        org = g.get_organization(orgName)
    except GithubException as ghe:
        print(ghe)

    print("Members without 2fa:", orgName)
    try:
        members = org.get_members(filter_="2fa_disabled")
    except GithubException as ghe:
        print(ghe)
    for member in members:
        print(member.login)

    print("Outside colaborators without 2fa:", orgName)
    try:
        colaborators = org.get_outside_collaborators(filter_="2fa_disabled")
    except GithubException as ghe:
        print(ghe)
    for colaborator in colaborators:
        print(colaborator.login)

@click.command(name='create')
@click.argument('organization')
@click.argument('repository')
@click.argument('description')
@click.pass_context
def create(ctx, organization, repository, description):
    """Create a Github repo for within an Organizations."""
    token = config.get_setting("github", "token")
    g = Github(token)
    orgName = organization
    print("All repos for organization: ", orgName)
    try:
        org = g.get_organization(orgName)
    except GithubException as ghe:
        print(ghe)
    repos = org.get_repos()

    for repo in repos:
        if repo.name == repository:
            print("repo already exists")
            sys.exit(1)
    try:
        org.create_repo(
            repository,
            allow_rebase_merge=False,
            auto_init=False,
            description=description,
            has_issues=False,
            has_projects=False,
            has_wiki=False,
            private=False,
        )
    except GithubException as ghe:
        print(ghe)


github_cli.add_command(list)
github_cli.add_command(create)
github_cli.add_command(audit)
