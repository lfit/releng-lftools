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

__author__ = "DW Talton"

import json
import logging

import lftools.api.client as client
from lftools import config

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

    ############
    # Privileges
    def privilege_list(self):
        """List privileges."""
        result = self.get("service/local/privileges")[1]["data"]

        privilege_list = []
        for privilege in result:
            privilege_list.append([privilege["name"], privilege["id"]])

        privilege_list.sort()
        return privilege_list

    def privilege_create(self, name, description, repo):
        """Create a new privilege.

        :param name: the privilege name
        :param description: the privilege description
        :param repo: the repo to attach to the privilege
        """
        data = {
            "data": {
                "name": name,
                "description": description,
                "type": "target",
                "repositoryTargetId": "any",
                "repositoryId": repo,
                "repositoryGroupId": "",
                "method": ["create", "read", "update", "delete"],
            }
        }

        json_data = json.dumps(data)
        result = self.post("service/local/privileges_target", data=json_data)

        if result[0].status_code == 201:
            return "Privilege successfully created."

    def privilege_delete(self, privilege_id):
        """Delete a privilege.

        :param privilege_id: the ID of the privilege (from privilege list)
        """
        result = self.delete("service/local/privileges/{}".format(privilege_id))

        if result.status_code == 204:
            return "Privilege successfully deleted."

    ##############
    # Repositories
    def repo_list(self):
        """Get a list of repositories."""
        result = self.get("service/local/repositories")[1]["data"]

        repo_list = []
        for repo in result:
            repo_list.append([repo["name"], repo["repoType"], repo["provider"], repo["id"]])

        return repo_list

    def repo_create(self, repo_type, repo_id, repo_name, repo_provider, repo_policy, repo_upstream_url):
        """Add a new repo.

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
                "repoType": repo_type,
            }
        }

        if repo_type == "hosted":
            data["data"].update(
                {"checksumPolicy": "IGNORE", "downloadRemoteIndexes": False, "writePolicy": "ALLOW_WRITE_ONCE"}
            )
            if repo_provider == "site":
                data["data"].update(
                    {
                        "repoPolicy": "MIXED",
                        "writePolicy": "ALLOW_WRITE",
                        "indexable": False,
                    }
                )

        if repo_type == "proxy":
            data["data"].update(
                {
                    "artifactMaxAge": -1,
                    "autoBlockActive": True,
                    "checksumPolicy": "WARN",
                    "downloadRemoteIndexes": True,
                    "fileTypeValidation": True,
                    "metadataMaxAge": 1440,
                    "remoteStorage": {
                        "authentication": None,
                        "connectionSettings": None,
                        "remoteStorageUrl": repo_upstream_url,
                    },
                }
            )

        json_data = json.dumps(data)
        result = self.post("service/local/repositories", data=json_data)

        if result[0].status_code == 201:
            return "Repo successfully created."
        else:
            return "Failed to create new repository"

    def repo_delete(self, repo_id):
        """Permanently delete a repo.

        :param repo_id: the ID of the repo from repo list.
        """
        result = self.delete("service/local/repositories/{}".format(repo_id))

        if result.status_code == 204:
            return "Repo successfully deleted."
        else:
            exit(1)

    #######
    # Roles
    def role_list(self):
        """List all roles."""
        result = self.get("service/local/roles")[1]

        role_list = []
        for role in result["data"]:
            # wacky string concat is to provide the right format
            # so that tabulate will iterate the string at the newline
            # breaks and show multiline columns in a nice way
            roles_string = ""
            privs_string = ""
            if "roles" in role:
                for roles in role["roles"]:
                    roles_string += roles + "\n"

            if "privileges" in role:
                for privs in role["privileges"]:
                    privs_string += privs + "\n"

            role_list.append([role["id"], role["name"], roles_string, privs_string])

        return role_list

    def role_create(self, role_id, role_name, role_description, roles_list=None, privs_list=None):
        """Create a new role.

        :param role_id: the ID name of the role (string)
        :param role_name: the actual name of the role
        :param role_description: the description of the role
        :param roles_list: (optional) a list of existing roles to attach to this role
        :param privs_list: (optional) a list of existing privs to attach to this role
        """
        data = {
            "data": {
                "id": role_id,
                "name": role_name,
                "description": role_description,
                "sessionTimeout": 0,
                "userManaged": True,
            }
        }

        if roles_list:
            data["data"]["roles"] = roles_list.split(",")

        if privs_list:
            data["data"]["privileges"] = privs_list.split(",")

        json_data = json.dumps(data)
        result = self.post("service/local/roles", data=json_data)

        if result[0].status_code == 201:
            return "Role successfully created."

        return result

    def role_delete(self, role_id):
        """Permanently delete a role.

        :param role_id: The ID of the role to delete (from role list)
        """
        result = self.delete("service/local/roles/{}".format(role_id))

        if result.status_code == 204:
            return "Role successfully deleted."

    #######
    # Users
    def user_list(self):
        """List all users."""
        result = self.get("service/local/plexus_users/allConfigured")[1]["data"]
        user_list = []
        for user in result:
            role_list = []
            for role in user["roles"]:
                role_list.append([role["roleId"]])

            user_list.append([user["userId"], user["firstName"], user["lastName"], user["status"], role_list])

        return user_list

    def user_create(self, username, firstname, lastname, email, roles, password=None):
        """Add a new user.

        :param username: the username
        :param firstname: the user's first name
        :param lastname: the user's last name
        :param email: the user's email address
        :param roles: a comma-separated list of roles to add the user to
        """
        role_list = roles.split(",")
        data = {
            "data": {
                "userId": username,
                "firstName": firstname,
                "lastName": lastname,
                "status": "active",
                "email": email,
                "roles": role_list,
            }
        }

        if password:
            data["data"]["password"] = password

        json_data = json.dumps(data)
        result = self.post("service/local/users", data=json_data)

        if result[0].status_code == 201:
            return "User successfully created."
        else:
            return "Failed to create new user"

    def user_delete(self, username):
        """Permanently delete a user.

        :param username: The username to delete (from user list)
        """
        result = self.delete("service/local/users/{}".format(username))

        if result.status_code == 204:
            return "User successfully deleted."
