# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################

"""Nexus3 REST API interface."""
import json
import logging

from lftools import config
import lftools.api.client as client

log = logging.getLogger(__name__)


class Nexus(client.RestApi):
    """API endpoint wrapper for Nexus3."""
    def __init__(self, **params):
        """Initialize the class."""
        self.params = params
        self.fqdn = self.params['fqdn']
        if 'creds' not in self.params:
            creds = {
                'authtype': 'basic',
                'username': config.get_setting(self.fqdn, 'username'),
                'password': config.get_setting(self.fqdn, 'password'),
                'endpoint': config.get_setting(self.fqdn, 'endpoint')
            }
            params['creds'] = creds

        super(Nexus, self).__init__(**params)

    def list_assets(self, repository, **kwargs):
        result = self.get('v1/assets?repository={}'.format(repository))[1]['items']
        if not result:
            return "This repository has no assets"
        else:
            item_list = []
            for item in result:
                item_list.append(item['path'])
            return item_list

    def list_blobstores(self, **kwargs):
        result = self.get('beta/blobstores')[1]
        list_of_blobstores = []
        for blob in result:
            list_of_blobstores.append(blob['name'])
        return list_of_blobstores

    def list_components(self, repository, **kwargs):
        result = self.get('v1/components?repository={}'.format(repository))[1]['items']
        if not result:
            return "This repository has no components"
        else:
            return result

    def list_privileges(self, **kwargs):
        result = self.get('beta/security/privileges')[1]
        list_of_privileges = []
        for privilege in result:
            list_of_privileges.append([privilege['type'], privilege['name'], privilege['description'], privilege['readOnly']])
        return list_of_privileges

    def list_repositories(self, **kwargs):
        result = self.get('v1/repositories')[1]
        list_of_repositories = []
        for repository in result:
            list_of_repositories.append(repository['name'])
        return list_of_repositories

    def list_roles(self, **kwargs):
        result = self.get('beta/security/roles')[1]
        list_of_roles = []
        for role in result:
            list_of_roles.append([role['name']])
        return list_of_roles

    def list_scripts(self, **kwargs):
        result = self.get('v1/script')[1]
        list_of_scripts = []
        for script in result:
            list_of_scripts.append(script['name'])
        return list_of_scripts

    def list_tasks(self, **kwargs):
        result = self.get('v1/tasks')[1]['items']
        list_of_tasks = []
        for task in result:
            list_of_tasks.append([task['name'], task['message'], task['currentState'], task['lastRunResult']])
        return list_of_tasks

    def list_user(self, username, **kwargs):
        result = self.get('beta/security/users?userId={}'.format(username))[1]
        user_info = []
        for user in result:
            user_info.append([user['userId'],
                                  user['firstName'],
                                  user['lastName'],
                                  user['emailAddress'],
                                  user['status'],
                                  user['roles']
                                  ])
        return user_info

    def list_users(self, **kwargs):
        result = self.get('beta/security/users')[1]
        list_of_users = []
        for user in result:
            list_of_users.append([user['userId'],
                                  user['firstName'],
                                  user['lastName'],
                                  user['emailAddress'],
                                  user['status'],
                                  user['roles']
                                  ])
        return list_of_users

    def create_role(self, name, description, privileges, roles):
        list_of_privileges = privileges.split(",")
        list_of_roles = roles.split(",")

        data = {
            "id": name,
            "name": name,
            "description": description,
            "privileges": list_of_privileges,
            "roles": list_of_roles
        }

        json_data = json.dumps(data, indent=4)
        result = self.post('beta/security/roles', data=json_data)

        if result[0].status_code == 200:
            return "Role {} created".format(name)
        else:
            return "Failed to create role"

