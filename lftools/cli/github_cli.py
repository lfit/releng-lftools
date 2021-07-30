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
from github import Github, GithubException

from lftools import config
from lftools.github_helper import helper_list, helper_user_github, prvotes


@click.group()
@click.pass_context
def github_cli(ctx):
    """GITHUB TOOLS."""
    pass


@click.command(name="submit-pr")
@click.argument("organization")
@click.argument("repo")
@click.argument("pr", type=int)
@click.pass_context
def submit_pr(ctx, organization, repo, pr):
    """Submit a pr if mergeable."""
    if config.get_setting("github." + organization, "token"):
        token = config.get_setting("github." + organization, "token")
    else:
        token = config.get_setting("github", "token")

    g = Github(token)
    orgName = organization
    try:
        org = g.get_organization(orgName)
    except GithubException as ghe:
        print(ghe)

    repo = org.get_repo(repo)
    pr_mergable = repo.get_pull(pr).mergeable

    if pr_mergable:
        print(pr_mergable)
        repo.get_pull(pr).merge(commit_message="Vote Completed, merging INFO file")
    else:
        print("PR NOT MERGABLE {}".format(pr_mergable))
        sys.exit(1)


@click.command(name="votes")
@click.argument("organization")
@click.argument("repo")
@click.argument("pr", type=int)
@click.pass_context
def votes(ctx, organization, repo, pr):
    """Helper for votes."""
    approval_list = prvotes(organization, repo, pr)
    print("Approvals:", approval_list)


@click.command(name="list")
@click.argument("organization")
@click.option("--audit", is_flag=True, required=False, help="List members without 2fa")
@click.option("--repos", is_flag=True, required=False, help="List all repos")
@click.option("--full", is_flag=True, required=False, help="All members and their respective teams")
@click.option("--teams", is_flag=True, required=False, help="List avaliable teams")
@click.option("--team", type=str, required=False, help="List members of a team")
@click.option("--repofeatures", is_flag=True, required=False, help="List enabled features for repos in an org")
@click.pass_context
def list(ctx, organization, repos, audit, full, teams, team, repofeatures):
    """List options for github org repos."""
    helper_list(ctx, organization, repos, audit, full, teams, team, repofeatures)


@click.command(name="create-repo")
@click.argument("organization")
@click.argument("repository")
@click.argument("description")
@click.option("--has_issues", is_flag=True, required=False, help="Repo should have issues")
@click.option("--has_projects", is_flag=True, required=False, help="Repo should have projects")
@click.option("--has_wiki", is_flag=True, required=False, help="Repo should have wiki")
@click.pass_context
def createrepo(ctx, organization, repository, description, has_issues, has_projects, has_wiki):
    """Create a Github repo within an Organization.

    By default has_issues has_wiki and has_projects is set to false.
    See --help to create a repo with these enabled.
    """
    if config.get_setting("github." + organization, "token"):
        token = config.get_setting("github." + organization, "token")
    else:
        token = config.get_setting("github", "token")

    g = Github(token)
    orgName = organization
    has_issues = has_issues or False
    has_wiki = has_wiki or False
    has_projects = has_projects or False
    print("Creating repo under organization: ", orgName)
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
            has_issues=has_issues,
            has_projects=has_projects,
            has_wiki=has_wiki,
            private=False,
        )
    except GithubException as ghe:
        print(ghe)


@click.command(name="update-repo")
@click.argument("organization")
@click.argument("repository")
@click.option("--has_issues", is_flag=True, required=False, help="Repo should have issues")
@click.option("--has_projects", is_flag=True, required=False, help="Repo should have projects")
@click.option("--has_wiki", is_flag=True, required=False, help="Repo should have wiki")
@click.option("--add_team", type=str, required=False, help="Add team to repo")
@click.option("--remove_team", type=str, required=False, help="remove team from repo")
@click.pass_context
def updaterepo(ctx, organization, repository, has_issues, has_projects, has_wiki, add_team, remove_team):
    """Update a Github repo within an Organization.

    By default has_issues has_wiki and has_projects is set to false.
    See --help to use this command to enable these options.
    """
    if config.get_setting("github." + organization, "token"):
        token = config.get_setting("github." + organization, "token")
    else:
        token = config.get_setting("github", "token")
    g = Github(token)
    orgName = organization

    has_issues = has_issues or False
    has_wiki = has_wiki or False
    has_projects = has_projects or False

    try:
        org = g.get_organization(orgName)
    except GithubException as ghe:
        print(ghe)

    repos = org.get_repos()

    if has_wiki or has_issues or has_projects:
        for repo in repos:
            if repo.name == repository:
                repo.edit(has_issues=has_issues)
                repo.edit(has_wiki=has_wiki)
                repo.edit(has_wiki=has_projects)

    if add_team or remove_team:
        teams = org.get_teams

        for repo in repos:
            if repo.name == repository:
                repo_actual = repo

        try:
            repo_actual
        except NameError:
            print("repo not found")
            exit(1)

        for team in teams():
            if team.name == add_team:
                print(team.id)
                team.add_to_repos(repo_actual)
                team.set_repo_permission(repo_actual, "write")
            if team.name == remove_team:
                print(team.id)
                team.remove_from_repos(repo_actual)


@click.command(name="create-team")
@click.argument("organization")
@click.argument("name")
@click.argument("privacy")
@click.option("--repo", type=str, required=False, help="Assign team to repo")
@click.pass_context
def createteam(ctx, organization, name, repo, privacy):
    """Create a Github team within an Organization.

    Privacy should be set to closed
    This allows us to control group membership.
    """
    if config.get_setting("github." + organization, "token"):
        token = config.get_setting("github." + organization, "token")
    else:
        token = config.get_setting("github", "token")

    g = Github(token)
    orgName = organization
    print("Creating team {} for repo {} under organization {} ".format(name, repo, orgName))
    try:
        org = g.get_organization(orgName)
    except GithubException as ghe:
        print(ghe)

    if repo:
        try:
            repos = org.get_repos
        except GithubException as ghe:
            print(ghe)

        my_repos = [repo]
        repos = [repo for repo in repos() if repo.name in my_repos]
        for repo in repos:
            print(repo)
        if repos:
            print("repo found")
        else:
            print("repo not found")
            sys.exit(1)

    try:
        teams = org.get_teams
    except GithubException as ghe:
        print(ghe)

    for team in teams():
        if team.name == name:
            print("team {} already exists".format(team))
            sys.exit(1)

    if repo:
        try:
            org.create_team(name=name, repo_names=repos, privacy=privacy)
        except GithubException as ghe:
            print(ghe)

    if not repo:
        try:
            org.create_team(name=name, privacy=privacy)
        except GithubException as ghe:
            print(ghe)


@click.command(name="user")
@click.argument("organization")
@click.argument("user")
@click.argument("team")
@click.option("--delete", is_flag=True, required=False, help="Remove user from org")
@click.option("--admin", is_flag=True, required=False, help="User is admin for org, or a maintaner of a team")
@click.pass_context
def user(ctx, organization, user, team, delete, admin):
    """Add and Remove users from an org team."""
    helper_user_github(ctx, organization, user, team, delete, admin)


github_cli.add_command(submit_pr)
github_cli.add_command(votes)
github_cli.add_command(list)
github_cli.add_command(createteam)
github_cli.add_command(createrepo)
github_cli.add_command(updaterepo)
github_cli.add_command(user)
