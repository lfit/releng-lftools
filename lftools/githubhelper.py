# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Github stub."""

from __future__ import print_function

import sys

from github import Github
from github import GithubException

from lftools import config


def prvotes(organization, repo, pr):
    """Get votes on a github pr."""
    token = config.get_setting("github", "token")
    g = Github(token)
    orgName = organization
    try:
        org = g.get_organization(orgName)
    except GithubException as ghe:
        print(ghe)

    repo = org.get_repo(repo)
    approval_list = []
    author = repo.get_pull(pr).user.login
    approval_list.append(author)

    pr_mergable = repo.get_pull(pr).mergeable
    print("MERGEABLE:", pr_mergable)

    approvals = repo.get_pull(pr).get_reviews()
    for approve in approvals:
        if approve.state == ("APPROVED"):
            approval_list.append(approve.user.login)
    return(approval_list)


def helper_list(organization, repos, audit, full, teams, team, repofeatures):
    """Moved this to helper, but bc of click I cant not pass options strings."""
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

    if team:
        try:
            teams = org.get_teams
        except GithubException as ghe:
            print(ghe)
        for t in teams():
            if t.name == team:
                print("{}".format(t.name))
                for user in t.get_members():
                    print("  - '{}'".format(user.login))


def helper_list_minimal(organization, team):
    """Minimal list helper that only needs to be passed 2 args."""
    token = config.get_setting("github", "token")
    g = Github(token)
    orgName = organization

    try:
        org = g.get_organization(orgName)
    except GithubException as ghe:
        print(ghe)

    team_members = []
    if team:
        try:
            teams = org.get_teams
        except GithubException as ghe:
            print(ghe)
        for t in teams():
            if t.name == team:
                print("{}".format(t.name))
                for user in t.get_members():
                    team_members.append(user.login)
                    print("  - '{}'".format(user.login))
    return(team_members)

# Code duplication here, is due to click requiring all the vars to be passed, so I had to created
# Ugly simplified versions. I will sort this out. file under teechnical debt.


def helper_add(organization, user, team):
    """Minimal add user to group function."""
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
    try:
        is_member = org.has_in_members(user_object)
        print("Is {} a member of org {}".format(user, is_member))
    except GithubException as ghe:
        print(ghe)
    try:
        teams = org.get_teams
    except GithubException as ghe:
        print(ghe)
    for t in teams():
        if t.name == team:
            this_team = t
    team = org.get_team(this_team.id)
    teams = []
    teams.append(team)
    if is_member:
        try:
            team.add_membership(member=user_object, role="member")
        except GithubException as ghe:
            print(ghe)
    if not is_member:
        try:
            org.invite_user(user=user_object, teams=teams)
        except GithubException as ghe:
            print(ghe)


def helper_delete(organization, user, team):
    """Minimal remove user from group function."""
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
    try:
        is_member = org.has_in_members(user_object)
        print("Is {} a member of org {}".format(user, is_member))
    except GithubException as ghe:
        print(ghe)
    try:
        teams = org.get_teams
    except GithubException as ghe:
        print(ghe)
    for t in teams():
        if t.name == team:
            this_team = t
    team = org.get_team(this_team.id)

    if is_member:
        try:
            team.remove_membership(user_object)
        except GithubException as ghe:
            print(ghe)
    else:
        print("{} is not a member of org cannot delete".format(user))
        # TODO add revoke invite
        print("Code does not handle revoking invitations.")
