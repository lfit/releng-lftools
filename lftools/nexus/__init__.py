# -*- code: utf-8 -*-
# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
# vim: sw=4 ts=4 sts=4 et :


"""Library for working with Sonatype Nexus REST API."""

__author__ = 'Andrew Grimberg'
__license__ = 'Apache 2.0'
__copyright__ = 'Copyright 2017 Andrew Grimberg'

import json

import requests
from requests.auth import HTTPBasicAuth


class Nexus:
    """Nexus class to handle communicating with Nexus over a rest api."""

    def __init__(self, baseurl=None, username=None, password=None):
        """Initialize Nexus instance."""
        self.baseurl = baseurl

        if username and password:
            self.add_credentials(username, password)
        else:
            self.auth = None

        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    def add_credentials(self, username, password):
        """Create an authentication object to be used."""
        self.auth = HTTPBasicAuth(username, password)

    def add_baseurl(self, url):
        """Set the base URL for nexus."""
        self.baseurl = url

    def get_target(self, name):
        """Get the ID of a given target name."""
        url = '/'.join([self.baseurl, 'service/local/repo_targets'])
        targets = requests.get(url, auth=self.auth, headers=self.headers).json()

        for priv in targets['data']:
            if priv['name'] == name:
                return priv['id']
        raise LookupError("No target found named '{}'".format(name))

    def create_target(self, name, patterns):
        """Create a target with the given patterns."""
        url = '/'.join([self.baseurl, 'service/local/repo_targets'])

        target = {
            'data': {
                'contentClass': 'any',
                'patterns': patterns,
                'name': name,
            }
        }

        json_data = json.dumps(target).encode(encoding='latin-1')

        r = requests.post(url, auth=self.auth, headers=self.headers, data=json_data)

        if r.status_code != requests.codes.created:
            raise Exception("Target not created for '{}', code '{}'".format(name, r.status_code))

        return r.json()['data']['id']

    def get_priv(self, name, priv):
        """Get the ID for the privilege with the given name."""
        url = '/'.join([self.baseurl, 'service/local/privileges'])

        search_name = "{} - ({})".format(name, priv)
        privileges = requests.get(url, auth=self.auth, headers=self.headers).json()

        for priv in privileges['data']:
            if priv['name'] == search_name:
                return priv['id']

        raise LookupError("No privilege found named '{}'".format(name))

    def create_priv(self, name, target_id, priv):
        """Create a given privilege.

        Privilege must be one of the following:

        create
        read
        delete
        update
        """
        url = '/'.join([self.baseurl, 'service/local/privileges_target'])

        privileges = {
            'data': {
                'name': name,
                'description': name,
                'method': [
                        priv,
                    ],
                'repositoryGroupId': '',
                'repositoryId': '',
                'repositoryTargetId': target_id,
                'type': 'target',
            }
        }

        json_data = json.dumps(privileges).encode(encoding='latin-1')
        r = requests.post(url, auth=self.auth, headers=self.headers, data=json_data)
        privileges = r.json()

        if r.status_code != requests.codes.created:
            raise Exception("Privilege not created for '{}', code '{}'".format(name, r.status_code))

        return privileges['data'][0]['id']

    def get_role(self, name):
        """Get the id of a role with a given name."""
        url = '/'.join([self.baseurl, 'service/local/roles'])
        roles = requests.get(url, auth=self.auth, headers=self.headers).json()

        for role in roles['data']:
            if role['name'] == name:
                return role['id']

        raise LookupError("No role with name '{}'".format(name))

    def create_role(self, name, privs):
        """Create a role with the given privileges."""
        url = '/'.join([self.baseurl, 'service/local/roles'])

        role = {
            'data': {
                'id': name,
                'name': name,
                'description': name,
                'privileges': privs,
                'roles': [
                        'repository-any-read',
                    ],
                'sessionTimeout': 60,
            }
        }

        json_data = json.dumps(role).encode(encoding='latin-1')

        r = requests.post(url, auth=self.auth, headers=self.headers, data=json_data)

        if r.status_code != requests.codes.created:
            raise Exception("Role not created for '{}', code '{}'".format(name, r.status_code))

        return r.json()['data']['id']

    def get_user(self, user_id):
        """Determine if a user with a given userId exists."""
        url = '/'.join([self.baseurl, 'service/local/users'])
        users = requests.get(url, auth=self.auth, headers=self.headers).json()

        for user in users['data']:
            if user['userId'] == user_id:
                return

        raise LookupError("No user with id '{}'".format(user_id))

    def create_user(self, name, domain, role_id, password, extra_roles=[]):
        """Create a Deployment user with a specific role_id and potentially extra roles.

        User is created with the nx-deployment role attached
        """
        url = '/'.join([self.baseurl, 'service/local/users'])

        user = {
            'data': {
                'userId': name,
                'email': "{}-deploy@{}".format(name, domain),
                'firstName': name,
                'lastName': 'Deployment',
                'roles': [
                        role_id,
                        'nx-deployment',
                    ],
                'password': password,
                'status': 'active',
            }
        }

        for role in extra_roles:
            user['data']['roles'].append(self.get_role(role))

        json_data = json.dumps(user).encode(encoding='latin-1')

        user = requests.post(url, auth=self.auth, headers=self.headers, data=json_data)

        if user.status_code != requests.codes.created:
            raise Exception("User not created for '{}', code '{}'".format(name, user.status_code))

    def get_repo_group(self, name):
        """Get the repository ID for a repo group that has a specific name."""
        url = '/'.join([self.baseurl, 'service/local/repo_groups'])

        repos = requests.get(url, auth=self.auth, headers=self.headers).json()

        for repo in repos['data']:
            if repo['name'] == name:
                return repo['id']

        raise LookupError("No repository group named '{}'".format(name))

    def get_repo_group_details(self, repoId):
        """Get the current configuration of a given repo group with a specific ID."""
        url = '/'.join([self.baseurl, 'service/local/repo_groups', repoId])

        return requests.get(url, auth=self.auth, headers=self.headers).json()['data']

    def update_repo_group_details(self, repoId, data):
        """Update the given repo group with new configuration."""
        url = '/'.join([self.baseurl, 'service/local/repo_groups', repoId])

        repo = {
            'data': data
        }

        json_data = json.dumps(repo).encode(encoding='latin-1')

        requests.put(url, auth=self.auth, headers=self.headers, data=json_data)
