# -*- code: utf-8 -*-
"""Github tools cmd module."""
# @License EPL-1.0 <http://spdx.org/licenses/EPL-1.0>
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################

__author__ = 'Jeremy Phelps'
import logging
import sys

import requests
import yaml

from lftools.github import GitHub

log = logging.getLogger(__name__)

def github_user(admin_config_file):
    """Set up an authenticated Github User.

    arg string admin_congif_file: Path to administrative config file
    containing Github api URL and token.
    """
    with open(admin_config_file, 'r') as admin_config_f:
        admin_config = yaml.safe_load(admin_config_f)

    for setting in ['base_url', 'token']:
        if not setting in admin_config:
            sys.exit('{} needs to be defined'.format(setting))

def protect_branches(config_file, admin_config_file, repo_name):
    """Protect repository branches via the Github api."""
    with open(config_file, 'r') as config_f:
        configs = yaml.safe_load(config_f)

    for hook in configs:
        print(hook)
        for key in hook:
            print(key)
            branch_name = hook[key]['name']
            enabled = hook[key]['enabled']
            enforcement_level = hook[key]['required_status_checks']['enforcement_level']
            contexts = hook[key]['required_status_checks']['contexts']

            # API CALL
            print("HI I CALLED THE API")
#            except KeyError as error:
#                sys.exit('Key Error: {}'.format(error))

def create_webhooks(config_file, admin_config_file, repo_name):
    """Create a webhook via the Github api."""
    with open(config_file, 'r') as config_f:
        configs = yaml.safe_load(config_f)

    for hook in configs:
        for key in hook:
            try:
                print("hello")
            except KeyError as error:
                sys.exit('Key Error: {}'.format(error))

def _admin_config(admin_config_file):
    with open(admin_config_file, 'r') as admin_config_f:
        admin_config = yaml.safe_load(admin_config_f)
    try:
        base_url = admin_config['base_url']
        api_token = admin_config['token']
        username = admin_config['username']
    except KeyError as e:
        log.info('KeyError: %s' % str(e))
    return base_url, username, api_token

def get_rate_limit_status(admin_config_file):
    base_url, username, api_token = _admin_config(admin_config_file)
    _github = GitHub(baseurl=base_url, username=username, password=api_token)
    rate_limit = _github.get_rate_limit_status(username)
    for key in rate_limit.headers:
        print('{}: {}'.format(key, rate_limit.headers[key]))

def get_org_members(org_name, admin_config_file):
    base_url, username, api_token = _admin_config(admin_config_file)
    _github = GitHub(baseurl=base_url, username=username, password=api_token)
    org_members = _github.get_org_members(org_name)
    print(len(org_members))
    for member in org_members:
        print(member['login'])
        print(member['html_url'])
        print()

def get_org_repos(org_name, admin_config_file):
    base_url, username, api_token = _admin_config(admin_config_file)
    _github = GitHub(baseurl=base_url, username=username, password=api_token)
    org_repos = _github.get_org_repos(org_name)
    print(len(org_repos))
    for repo in org_repos:
        print(repo)

def get_org_teams(org_name, admin_config_file):
    base_url, username, api_token = _admin_config(admin_config_file)
    accept_header = 'application/vnd.github.hellcat-preview+json'
    _github = GitHub(baseurl=base_url, username=username,
                     password=api_token, accept_header=accept_header)
    org_teams = _github.get_org_teams(org_name)
    return org_teams

def get_team_members(team_id, admin_config_file):
    base_url, username, api_token = _admin_config(admin_config_file)
    accept_header = 'application/vnd.github.hellcat-preview+json'
    _github = GitHub(baseurl=base_url, username=username,
                     password=api_token, accept_header=accept_header)
    team_members = _github.get_team_members(team_id)
    return team_members

def get_repo_collaborators(org_name, repo, admin_config_file):
    base_url, username, api_token = _admin_config(admin_config_file)
    accept_header = 'application/vnd.github.hellcat-preview+json'
    _github = GitHub(baseurl=base_url, username=username,
                     password=api_token, accept_header=accept_header)
    repo_collaborators = _github.get_repo_collaborators(org_name, repo)
    for collaborator in repo_collaborators:
        print(collaborator['login'])
    return repo_collaborators

def get_repo_contributors(owner, repo_id, admin_config_file):
    base_url, username, _ = _admin_config(admin_config_file)
    accept_header = 'application/vnd.github.hellcat-preview+json'
    _github = GitHub(baseurl=base_url, username=username, accept_header=accept_header)
    repo_contributors = _github.get_repo_contributors(owner, repo_id)
    for contributor in repo_contributors:
        print(contributor['author']['login'])
    return repo_contributors

def org_team_member_audit(org_name, admin_config_file):
    base_url, username, api_token = _admin_config(admin_config_file)
    accept_header = 'application/vnd.github.hellcat-preview+json'
    _github = GitHub(baseurl=base_url, username=username,
                     password=api_token, accept_header=accept_header)
    org_teams = _github.get_org_teams(org_name)
    for team in org_teams:
        team_members = _github.get_team_members(team['id'])
        print('{}:'.format(team['name']))
        for member in team_members:
            print('- {}'.format(member['login']))

def org_repo_audit(org_name, admin_config_file):
    base_url, username, api_token = _admin_config(admin_config_file)
    _github = GitHub(baseurl=base_url, username=username, password=api_token)
    org_repos = _github.get_org_repos(org_name)
    for repo in org_repos:
        print('{}:'.format(repo['id']))
        repo_collaborators = _github.get_repo_collaborators(username, repo['full_name'])
        print(repo_collaborators)