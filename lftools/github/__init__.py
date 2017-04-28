# -*- code: utf-8 -*-
# @License EPL-1.0 <http://spdx.org/licenses/EPL-1.0>
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""lftools GitHub package."""

__author__ = 'Jeremy Phelps'

import json

import requests
from requests.auth import HTTPBasicAuth

class GitHub:
    """GitHub class to facilitate API calls to GitHub."""

    def __init__(self, baseurl='https://api.github.com',
                 username=None, password=None,
                 accept_header='application/vnd.github.v3+json'):

        """Initialize GitHub."""
        self.baseurl = baseurl

        if username and password:
            self.add_credentials(username, password)
        else:
            self.auth = None

        self.headers = {
            'Accept': accept_header,
            'Content-Type': 'application/json',
            'User-Agent': username
        }

    def add_credentials(self, username, password):
        """HTTPBasicAuth Object setup."""
        self.auth = HTTPBasicAuth(username, password)

    def add_baseurl(self, url):
        """Set the base URL for GitHub."""
        self.baseurl = url
    
    def get_rate_limit_status(self, username):
        """Get the stats on API rate limiting"""
        url = ''.join([self.baseurl, '/%s' % username])
        rate_limit = requests.head(url, auth=self.auth, headers=self.headers)
        return rate_limit.content

    def get_org_members(self, org):
        """Get all the members of a GitHub organization"""
        url = ''.join([self.baseurl, '/orgs/%s/members' % org])
        members = requests.get(url, auth=self.auth, headers=self.headers).json()
        return members

    def get_org_repos(self, org):
        """Get all the repositories of a GitHub organization"""
        url = ''.join([self.baseurl, '/orgs/%s/repos' % org])
        repos = requests.get(url, auth=self.auth, headers=self.headers).json()
        return repos

    def get_org_teams(self, org):
        """Get all the repositories of a GitHub organization"""
        url = ''.join([self.baseurl, '/orgs/%s/teams?per_page=100' % org])
        teams = requests.get(url, auth=self.auth, headers=self.headers).json()
        return teams

    def get_repo_collaborators(self, org, repo):
        """Get all the collaborators of an organizations given repository"""
        url = ''.join([self.baseurl, '/repos/%s/%s/collaborators' % (org, repo)])
        collaborators = requests.get(url, auth=self.auth, headers=self.headers).json()
        return collaborators

    def get_repo_contributors(self, username, repo):
        """Get all the collaborators of an organizations given repository"""
        url = ''.join([self.baseurl, '/repos/%s/%s/stats/contributors' % (username, repo)])
        contributors = requests.get(url, auth=self.auth, headers=self.headers).json()
        return contributors

    def get_team_members(self, team_id):
        """Get all the members of a GitHub team"""
        url = ''.join([self.baseurl, '/teams/%s/members' % team_id])
        members = requests.get(url, auth=self.auth, headers=self.headers).json()
        return members
