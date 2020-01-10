# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################

"""Nexus2 REST API interface."""

__author__ = 'DW Talton'

import json
import logging

from lftools import config
import lftools.api.client as client

log = logging.getLogger(__name__)


class Nexus2(client.RestApi):
    """API endpoint wrapper for Nexus2."""

    def __init__(self, **params):
        """Initialize the class."""
        self.params = params
        self.fqdn = self.params["fqdn"]
        if "creds" not in self.params:
            creds = {
                "authtype": "basic",
                "username": config.get_setting(self.fqdn, "username"),
                "password": config.get_setting(self.fqdn, "password"),
                "endpoint": config.get_setting(self.fqdn, "endpoint"),
            }
            params["creds"] = creds

        super(Nexus2, self).__init__(**params)

###########
########### Privileges
    def privilege_list(self):
        pass

    def privilege_create(self):
        pass

    def privilege_details(self):
        pass

    def privilege_update(self):
        pass

    def privilege_delete(self):
        pass

###########
########### Repositories
    def repo_list(self):
        """Get a list of repositories."""
        result = self.get('repositories')[1]['data']

        repo_list = []
        for repo in result:
            repo_list.append([
                repo['name'],
                repo['repoType'],
                repo['provider'],
                repo['id']
            ])

        return repo_list

    def repo_create(self, repo_type, repo_id, repo_name, repo_provider, repo_policy, repo_upstream_url):
        """Add a new repo

        :param repo_type: the type of repo. Valid types are 'proxy' and 'hosted'
        :param repo_id: the ID for the repository
        :param repo_name: the name for the repository
        :param repo_provider: the provider type. Valid types are 'maven2' and 'site'
        :param repo_policy: the repo policy. Valid types are 'RELEASE', 'SNAPSHOT', 'MIXED'
        :param repo_upstream_url: the URL to an upstream repo when creating a proxy repo
        """

        # common data regardless of repo type
        data = {
            "data": {
                "browseable": True,
                "exposed": True,
                "id": repo_id,
                "indexable": True,
                "name": repo_name,
                "notFoundCacheTTL": 1440,
                "provider": repo_provider,
                "providerRole": "org.sonatype.nexus.proxy.repository.Repository",
                "repoPolicy": repo_policy,
                'repoType': repo_type
            }
        }


        if repo_type == "hosted":
            data['data'].update({
                "checksumPolicy": "IGNORE",
                "downloadRemoteIndexes": False,
                "writePolicy": "ALLOW_WRITE_ONCE"
            })
            if repo_provider == 'site':
                data['data'].update({
                    'repoPolicy': 'MIXED',
                    'writePolicy': 'ALLOW_WRITE',
                    'indexable': False,
                })

        if repo_type == 'proxy':
            data['data'].update({
                'artifactMaxAge': -1,
                'autoBlockActive': True,
                "checksumPolicy": "WARN",
                "downloadRemoteIndexes": True,
                'fileTypeValidation': True,
                'metadataMaxAge': 1440,
                'remoteStorage': {
                    'authentication': None,
                    'connectionSettings': None,
                    'remoteStorageUrl': repo_upstream_url
                }
            })


        # if repo_type == 'hosted':
        #     data = {
        #         "data": {
        #
        #             "checksumPolicy": "IGNORE",
        #             "downloadRemoteIndexes": False,
        #             "repoType": "hosted",
        #             "writePolicy": "ALLOW_WRITE_ONCE"
        #         }
        #     }
        json_data = json.dumps(data)


        result = self.post("repositories", data=json_data)
        if result[0].status_code == 201:
            return "Repo successfully created."
        else:
            return "Failed to create new repository"

    def repo_details(self):
        pass

    def repo_update(self):
        pass

    def repo_delete(self):
        pass

###########
########### Roles
    def role_list(self):
        pass

    def role_create(self):
        pass

    def role_details(self):
        pass

    def role_update(self):
        pass

    def role_delete(self):
        pass

###########
########### Users
    def user_list(self):
        # http://192.168.1.31:8081/nexus/service/local/plexus_users/allConfigured?_dc=1
        result = self.get('plexus_users/allConfigured')[1]['data']

        user_list = []
        for user in result:
            role_list = []
            for role in user['roles']:
                role_list.append([
                    role['roleId']
                ])

            user_list.append([
                user['userId'],
                user['firstName'],
                user['lastName'],
                user['status'],
                role_list
            ])

        return user_list

    def user_add(self):
        pass

    def user_details(self):
        """Determine if a user with a given userId exists."""
        url = os.path.join(self.baseurl, 'users')
        users = requests.get(url, auth=self.auth, headers=self.headers).json()

        result = self.get('users')

        for user in users['data']:
            if user['userId'] == user_id:
                return

        raise LookupError("No user with id '{}'".format(user_id))

    def user_update(self):
        pass

    def user_delete(self):
        pass
