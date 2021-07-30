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

import logging
import sys

from github import Github, GithubException

from lftools import config

log = logging.getLogger(__name__)


def helper_list(ctx, organization, repos, audit, full, teams, team, repofeatures):
    """List options for github org repos."""
    # Optionally pick token based on gitub org

    if config.has_section("github"):
        token = config.get_setting("github", "token")
    else:
        section = "github.{}".format(organization)
        token = config.get_setting(section, "token")

    g = Github(token)
    orgName = organization

    try:
        org = g.get_organization(orgName)
    except GithubException as ghe:
        log.error(ghe)

    # Extend this to check if a repo exists
    if repos:
        print("All repos for organization: ", orgName)
        repos = org.get_repos()
        for repo in repos:
            log.info(repo.name)

    if audit:
        log.info("{} members without 2fa:".format(orgName))
        try:
            members = org.get_members(filter_="2fa_disabled")
        except GithubException as ghe:
            log.error(ghe)
        for member in members:
            log.info(member.login)
        log.info("{} outside collaborators without 2fa:".format(orgName))
        try:
            collaborators = org.get_outside_collaborators(filter_="2fa_disabled")
        except GithubException as ghe:
            log.error(ghe)
        for collaborator in collaborators:
            log.info(collaborator.login)

    if repofeatures:
        repos = org.get_repos()
        for repo in repos:
            log.info("{} wiki:{} issues:{}".format(repo.name, repo.has_wiki, repo.has_issues))
            issues = repo.get_issues
            for issue in issues():
                log.info("{}".format(issue))

    if full:
        log.info("---")
        log.info("#  All owners for {}:".format(orgName))
        log.info("{}-owners:".format(orgName))

        try:
            members = org.get_members(role="admin")
        except GithubException as ghe:
            log.error(ghe)
        for member in members:
            log.info("  - '{}'".format(member.login))
        log.info("#  All members for {}".format(orgName))
        log.info("{}-members:".format(orgName))

        try:
            members = org.get_members()
        except GithubException as ghe:
            log.error(ghe)
        for member in members:
            log.info("  - '{}'".format(member.login))
        log.info("#  All members and all teams for {}".format(orgName))

        try:
            teams = org.get_teams
        except GithubException as ghe:
            log.error(ghe)
        for team in teams():
            log.info("{}:".format(team.name))
            for user in team.get_members():
                log.info("  - '{}'".format(user.login))
            log.info("")
        teams = None

    if teams:
        try:
            teams = org.get_teams
        except GithubException as ghe:
            log.error(ghe)
        for team in teams():
            log.info("{}".format(team.name))

    if team:
        try:
            teams = org.get_teams
        except GithubException as ghe:
            log.error(ghe)

        team_members = []

        for t in teams():
            if t.name == team:
                log.info("{}".format(t.name))
                for user in t.get_members():
                    team_members.append(user.login)
                    log.info("  - '{}'".format(user.login))

        return team_members


def prvotes(organization, repo, pr):
    """Get votes on a github pr."""
    token = config.get_setting("github", "token")
    g = Github(token)
    orgName = organization
    try:
        org = g.get_organization(orgName)
    except GithubException as ghe:
        log.error(ghe)

    repo = org.get_repo(repo)
    approval_list = []
    author = repo.get_pull(pr).user.login
    approval_list.append(author)

    pr_mergable = repo.get_pull(pr).mergeable
    log.info("MERGEABLE: {}".format(pr_mergable))

    approvals = repo.get_pull(pr).get_reviews()
    for approve in approvals:
        if approve.state == ("APPROVED"):
            approval_list.append(approve.user.login)
    return approval_list


def helper_user_github(ctx, organization, user, team, delete, admin):
    """Add and Remove users from an org team."""
    token = config.get_setting("github", "token")
    g = Github(token)
    orgName = organization
    try:
        org = g.get_organization(orgName)
    except GithubException as ghe:
        log.error(ghe)
    try:
        user_object = g.get_user(user)
        log.info(user_object)
    except GithubException as ghe:
        log.error(ghe)
        log.info("user {} not found".format(user))
        sys.exit(1)
    # check if user is a member
    try:
        is_member = org.has_in_members(user_object)
        log.info("Is {} a member of org {}".format(user, is_member))
    except GithubException as ghe:
        log.error(ghe)
    # get teams
    try:
        teams = org.get_teams
    except GithubException as ghe:
        log.error(ghe)

    # set team to proper object
    my_teams = [team]
    this_team = [team for team in teams() if team.name in my_teams]
    for t in this_team:
        team_id = t.id
    team = org.get_team(team_id)
    teams = []
    teams.append(team)

    if delete:
        if is_member:
            try:
                team.remove_membership(user_object)
            except GithubException as ghe:
                log.error(ghe)
            log.info("Removing user {} from {}".format(user_object, team))
        else:
            log.info("{} is not a member of org cannot delete".format(user))
            # TODO add revoke invite
            log.info("Code does not handle revoking invitations.")

    if user and not delete:
        if admin and is_member:
            try:
                team.add_membership(member=user_object, role="maintainer")
            except GithubException as ghe:
                log.error(ghe)
        if admin and not is_member:
            try:
                org.invite_user(user=user_object, role="admin", teams=teams)
            except GithubException as ghe:
                log.error(ghe)
            log.info("Sending Admin invite to {} for {}".format(user_object, team))

        if not admin and is_member:
            try:
                team.add_membership(member=user_object, role="member")
            except GithubException as ghe:
                log.error(ghe)

        if not admin and not is_member:
            try:
                org.invite_user(user=user_object, teams=teams)
            except GithubException as ghe:
                log.error(ghe)
            log.info("Sending invite to {} for {}".format(user_object, team))
