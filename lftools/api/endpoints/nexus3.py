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

__author__ = "DW Talton"

import json
import logging

import lftools.api.client as client
from lftools import config, helpers

log = logging.getLogger(__name__)


class Nexus3(client.RestApi):
    """API endpoint wrapper for Nexus3."""

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

        super(Nexus3, self).__init__(**params)

    def create_role(self, name, description, privileges, roles):
        """Create a new role.

        :param name: the role name
        :param description: the role description
        :param privileges: privileges assigned to this role
        :param roles: other roles attached to this role
        """
        list_of_privileges = privileges.split(",")
        list_of_roles = roles.split(",")

        data = {
            "id": name,
            "name": name,
            "description": description,
            "privileges": list_of_privileges,
            "roles": list_of_roles,
        }

        json_data = json.dumps(data, indent=4)
        result = self.post("beta/security/roles", data=json_data)

        if result[0].status_code == 200:
            return "Role {} created".format(name)
        else:
            return "Failed to create role"

    def create_script(self, name, content):
        """Create a new script.

        :param name: script name
        :param content: content of the script (groovy code)
        """
        data = {"name": name, "content": content, "type": "groovy"}

        json_data = json.dumps(data)
        result = self.post("v1/script", data=json_data)

        if result.status_code == 204:
            return "Script {} successfully added.".format(name)
        else:
            return "Failed to create script {}".format(name)

    def create_tag(self, name, attributes):
        """Create a new tag.

        :param name: the tag name
        :param attributes: the tag's attributes
        """
        data = {
            "name": name,
        }

        if attributes is not None:
            data["attributes"] = attributes

        json_data = json.dumps(data)
        result = self.post("v1/tags", data=json_data)[0]

        if result.status_code == 200:
            return "Tag {} successfully added.".format(name)
        else:
            return "Failed to create tag {}".format(name)

    def create_user(self, username, first_name, last_name, email_address, roles, password=None):
        """Create a new user.

        @param username:
        @param first_name:
        @param last_name:
        @param email:
        @param status:
        @param roles:
        @param password:
        """
        list_of_roles = roles.split(",")
        data = {
            "userId": username,
            "firstName": first_name,
            "lastName": last_name,
            "emailAddress": email_address,
            "status": "active",
            "roles": list_of_roles,
        }

        if password:
            data["password"] = password
        else:
            data["password"] = helpers.generate_password()

        json_data = json.dumps(data)
        result = self.post("beta/security/users", data=json_data)[0]

        if result.status_code == 200:
            return "User {} successfully created with password {}".format(username, data["password"])
        else:
            log.error("Failed to create user {}".format(username))

    def delete_script(self, name):
        """Delete a script from the server.

        :param name: the script name
        """
        result = self.delete("v1/script/{}".format(name))

        if result.status_code == 204:
            return "Successfully deleted {}".format(name)
        else:
            return "Failed to delete script {}".format(name)

    def delete_tag(self, name):
        """Delete a tag from the server.

        :param name: the tag's name
        """
        result = self.delete("v1/tags/{}".format(name))

        if result.status_code == 204:
            return "Tag {} successfully deleted.".format(name)
        else:
            return "Failed to delete tag {}.".format(name)

    def delete_user(self, username):
        """Delete a user.

        @param username:
        """
        result = self.delete("beta/security/users/{}".format(username))

        if hasattr(result, "status_code"):
            if result.status_code == 204:
                return "Successfully deleted user {}".format(username)
        else:
            return "Failed to delete user {} with error: {}".format(username, result[1])

    def list_assets(self, repository, **kwargs):
        """List the assets of a given repo.

        :param repository: repo name
        """
        result = self.get("v1/assets?repository={}".format(repository))[1]["items"]
        if not result:
            return "This repository has no assets"
        else:
            item_list = []
            for item in result:
                item_list.append(item["path"])
            return item_list

    def list_blobstores(self, **kwargs):
        """List server blobstores."""
        result = self.get("beta/blobstores")[1]
        list_of_blobstores = []
        for blob in result:
            list_of_blobstores.append(blob["name"])
        return list_of_blobstores

    def list_components(self, repository, **kwargs):
        """List components from a repo.

        :param repository: the repo name
        """
        result = self.get("v1/components?repository={}".format(repository))[1]["items"]
        if not result:
            return "This repository has no components"
        else:
            return result

    def list_privileges(self, **kwargs):
        """List server-configured privileges."""
        result = self.get("beta/security/privileges")[1]
        list_of_privileges = []
        for privilege in result:
            list_of_privileges.append(
                [
                    privilege["type"],
                    privilege["name"],
                    privilege["description"],
                    privilege["readOnly"],
                ]
            )
        return list_of_privileges

    def list_repositories(self, **kwargs):
        """List server repositories."""
        result = self.get("v1/repositories")[1]
        list_of_repositories = []
        for repository in result:
            list_of_repositories.append(repository["name"])
        return list_of_repositories

    def list_roles(self, **kwargs):
        """List server roles."""
        result = self.get("beta/security/roles")[1]
        list_of_roles = []
        for role in result:
            list_of_roles.append([role["name"]])
        return list_of_roles

    def list_scripts(self, **kwargs):
        """List server scripts."""
        result = self.get("v1/script")[1]
        list_of_scripts = []
        for script in result:
            list_of_scripts.append(script["name"])
        return list_of_scripts

    def show_tag(self, name):
        """Get tag details.

        :param name: tag name
        :return:
        """
        result = self.get("v1/tags/{}".format(name))[1]
        return result

    def list_tags(self):
        """List all tag."""
        result = self.get("v1/tags")[1]
        list_of_tags = []
        token = result["continuationToken"]
        if token is not None:
            while token is not None:
                for tag in result["items"]:
                    list_of_tags.append(tag["name"])
                result = self.get("v1/tags?continuationToken={}".format(result["continuationToken"]))[1]
                token = result["continuationToken"]
        else:
            for tag in result["items"]:
                list_of_tags.append(tag["name"])

        if list_of_tags:
            return list_of_tags
        else:
            return "There are no tags"

    def list_tasks(self, **kwargs):
        """List all tasks."""
        result = self.get("v1/tasks")[1]["items"]
        list_of_tasks = []
        for task in result:
            list_of_tasks.append(
                [
                    task["name"],
                    task["message"],
                    task["currentState"],
                    task["lastRunResult"],
                ]
            )
        return list_of_tasks

    def list_user(self, username, **kwargs):
        """Show user details.

        :param username: the user's username
        """
        result = self.get("beta/security/users?userId={}".format(username))[1]
        user_info = []
        for user in result:
            user_info.append(
                [
                    user["userId"],
                    user["firstName"],
                    user["lastName"],
                    user["emailAddress"],
                    user["status"],
                    user["roles"],
                ]
            )
        return user_info

    def list_users(self, **kwargs):
        """List all users."""
        result = self.get("beta/security/users")[1]
        list_of_users = []
        for user in result:
            list_of_users.append(
                [
                    user["userId"],
                    user["firstName"],
                    user["lastName"],
                    user["emailAddress"],
                    user["status"],
                    user["roles"],
                ]
            )
        return list_of_users

    def staging_promotion(self, destination_repo, tag):
        """Promote repo assets to a new location.

        :param destination_repo: the repo to promote into
        :param tag: the tag used to identify the assets
        """
        data = {"tag": tag}
        json_data = json.dumps(data)
        result = self.post("v1/staging/move/{}".format(destination_repo), data=json_data)
        return result

    def read_script(self, name):
        """Get the contents of a script.

        :param name: the script name
        """
        result = self.get("v1/script/{}".format(name))

        if result[0].status_code == 200:
            return result[1]
        else:
            return "Failed to read script {}".format(name)

    def run_script(self, name):
        """Run a script on the server.

        :param name: the script name
        """
        result = self.post("v1/script/{}/run".format(name))

        if result[0].status_code == 200:
            return result[1]
        else:
            return "Failed to execute script {}".format(name)

    def search_asset(self, query, repository, details=False):
        """Search for an asset.

        :param query: querystring to use, eg myjar-1 to find myjar-1.2.3.jar
        :param repository: the repo to search in
        :param details: returns a fully-detailed json dump
        """
        data = {
            "q": query,
            "repository": repository,
        }
        json_data = json.dumps(data)
        result = self.get("v1/search/assets?q={}&repository={}".format(query, repository), data=json_data,)[
            1
        ]["items"]
        list_of_assets = []

        if details:
            return json.dumps(result, indent=4)

        for item in result:
            list_of_assets.append(item["path"])

        return list_of_assets

    def update_script(self, name, content):
        """Update an existing script on the server.

        :param name: script name
        :param content: new content for the script (groovy code)
        """
        data = {"name": name, "content": content, "type": "groovy"}

        json_data = json.dumps(data)

        result = self.put("v1/script/{}".format(name), data=json_data)

        if result.status_code == 204:
            return "Successfully updated {}".format(name)
        else:
            return "Failed to update script {}".format(name)
