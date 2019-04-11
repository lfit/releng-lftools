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
@click.option('--audit', is_flag=True, required=False,
              help='list members without 2fa')
@click.option('--repos', is_flag=True, required=False,
              help='list all repos')
@click.option('--full', is_flag=True, required=False,
              help='All members and their respective teams')
@click.option('--teams', is_flag=True, required=False,
              help='List avaliable teams')
@click.option('--disableissues', is_flag=True, required=False,
              help='Disable issues for all repos in an org')
@click.option('--repofeatures', is_flag=True, required=False,
              help='list enabled features for repos in an org')
@click.pass_context
def list(ctx, organization, repos, audit, full, teams, disableissues, repofeatures):
    """List an Organization's GitHub repos."""
    token = config.get_setting("github", "token")
    g = Github(token)
    orgName = organization

    try:
        org = g.get_organization(orgName)
    except GithubException as ghe:
        print(ghe)

    if repos:
        print("All repos for organization: ", orgName)
        repos = org.get_repos()
        for repo in repos:
            print(repo.name)

    if audit:
        print("{} members without 2fa:".format(orgName))
        try:
            members = org.get_members(filter_="2fa_disabled")
        except GithubException as ghe:
            print(ghe)
        for member in members:
            print(member.login)
        print("{} outside collaborators without 2fa:".format(orgName))
        try:
            collaborators = org.get_outside_collaborators(filter_="2fa_disabled")
        except GithubException as ghe:
            print(ghe)
        for collaborator in collaborators:
            print(collaborator.login)

    if repofeatures:
        repos = org.get_repos()
        for repo in repos:
            print("{} wiki:{} issues:{}".format(repo.name, repo.has_wiki, repo.has_issues))
            issues = repo.get_issues
            for issue in issues():
                print("{}".format(issue))

    if disableissues:
        repos = org.get_repos()
        for repo in repos:
            repo.edit(has_issues=False)

    if full:
        print("---")
        print("#  All owners for {}:".format(orgName))
        print("{}-owners:".format(orgName))

        try:
            members = org.get_members(role="admin")
        except GithubException as ghe:
            print(ghe)
        for member in members:
            print("  - '{}'".format(member.login))
        print("#  All members for {}".format(orgName))
        print("{}-members:".format(orgName))

        try:
            members = org.get_members()
        except GithubException as ghe:
            print(ghe)
        for member in members:
            print("  - '{}'".format(member.login))
        print("#  All members and all teams for {}".format(orgName))

        try:
            teams = org.get_teams
        except GithubException as ghe:
            print(ghe)
        for team in teams():
            print("{}:".format(team.name))
            for user in team.get_members():
                print("  - '{}'".format(user.login))
            print("")
        teams = None

    if teams:
        try:
            teams = org.get_teams
        except GithubException as ghe:
            print(ghe)
        for team in teams():
            print("{}".format(team.name))


# Add a switch so you can create a repo with diffrent settings.
@click.command(name='create-repo')
@click.argument('organization')
@click.argument('repository')
@click.argument('description')
@click.option('--sparse', is_flag=True, required=False,
              help='Repo does not need issues or a wiki.')
@click.option('--full', is_flag=True, required=False,
              help='Repo has issues and a wiki.')
@click.pass_context
def createrepo(ctx, organization, repository, description, sparse, full):
    """Create a Github repo within an Organization.

    Pass --sparse if repo is only for replication from gerrit
    Pass --full if repo is a standalone for github only projects.
    """
    token = config.get_setting("github", "token")
    g = Github(token)
    orgName = organization

    if not sparse or full:
        print("please secify one of --sparse or --full")
        sys.exit(1)

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
    if sparse:
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
    if full:
        try:
            org.create_repo(
                repository,
                allow_rebase_merge=False,
                auto_init=False,
                description=description,
                has_issues=True,
                has_projects=True,
                has_wiki=True,
                private=False,
            )
        except GithubException as ghe:
            print(ghe)


@click.command(name='create-team')
@click.argument('organization')
@click.argument('name')
@click.argument('repo')
@click.argument('privacy')
@click.pass_context
def createteam(ctx, organization, name, repo, privacy):
    """Create a Github team within an Organization."""
    token = config.get_setting("github", "token")
    g = Github(token)
    orgName = organization
    print("Creating team {} for repo {} under organization {} ".format(name, repo, orgName))
    try:
        org = g.get_organization(orgName)
    except GithubException as ghe:
        print(ghe)

    try:
        repos = org.get_repos
    except GithubException as ghe:
        print(ghe)

    try:
        teams = org.get_teams
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

    for team in teams():
        if team.name == name:
            print("team {} already exists".format(team))
            sys.exit(1)
    try:
        org.create_team(
            name=name,
            repo_names=repos,
            privacy=privacy
        )
    except GithubException as ghe:
        print(ghe)


@click.command(name='user')
@click.argument('organization')
@click.argument('user')
@click.argument('team')
@click.option('--delete', is_flag=True, required=False,
              help='remove user from org')
@click.option('--admin', is_flag=True, required=False,
              help='user is admin for org, or a maintaner of a team')
@click.pass_context
def user(ctx, organization, user, team, delete, admin):
    """Add and Remove users from an org team."""
    token = config.get_setting("github", "token")
    g = Github(token)
    orgName = organization
    try:
        org = g.get_organization(orgName)
    except GithubException as ghe:
        print(ghe)
    try:
        user_object = g.get_user(user)
        print(user_object)
    except GithubException as ghe:
        print(ghe)
        print("user {} not found".format(user))
        sys.exit(1)
    # check if user is a member
    try:
        is_member = org.has_in_members(user_object)
        print("Is {} a member of org {}".format(user, is_member))
    except GithubException as ghe:
        print(ghe)
    # get teams
    try:
        teams = org.get_teams
    except GithubException as ghe:
        print(ghe)

    my_teams = [team]
    teams = [team for team in teams() if team.name in my_teams]

    if delete:
        if is_member:
            for t in teams:
                team_id = (t.id)
            try:
                team = org.get_team(team_id)
                team.remove_membership(user_object)
            except GithubException as ghe:
                print(ghe)
        else:
            print("{} is not a member of org cannot delete".format(user))

    if user and not delete:
        if admin and is_member:
            try:
                team.add_membership(member=user_object, role="maintainer")
            except GithubException as ghe:
                print(ghe)
        if admin and not is_member:
            try:
                org.invite_user(user=user_object, role="admin", teams=teams)
            except GithubException as ghe:
                print(ghe)

        if not admin and is_member:
            try:
                team.add_membership(member=user_object, role="member")
            except GithubException as ghe:
                print(ghe)

        if not admin and not is_member:
            try:
                org.invite_user(user=user_object, teams=teams)
            except GithubException as ghe:
                print(ghe)


github_cli.add_command(list)
github_cli.add_command(createteam)
github_cli.add_command(createrepo)
github_cli.add_command(user)
