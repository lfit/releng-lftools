# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################

"""Gerrit REST API interface."""

import json
import logging
import os
import time
import urllib

import lftools.api.client as client
from lftools import config

log = logging.getLogger(__name__)


class Gerrit(client.RestApi):
    """API endpoint wrapper for Gerrit.

    Be sure to always include the trailing "/" when adding
    new methods.
    """

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

        super(Gerrit, self).__init__(**params)

    def add_file(self, fqdn, gerrit_project, filename, issue_id, file_location, **kwargs):
        """Add a file for review to a Project.

        File can be sourced from any location
        but only lands in the root of the repo.
        unless file_location is specified
        Example:

        gerrit_url gerrit.o-ran-sc.org
        gerrit_project test/test1
        filename /tmp/INFO.yaml
        file_location="somedir/example-INFO.yaml"
        """
        signed_off_by = config.get_setting(fqdn, "sob")
        basename = os.path.basename(filename)
        payload = self.create_change(basename, gerrit_project, issue_id, signed_off_by)

        if file_location:
            file_location = urllib.parse.quote(file_location, safe="", encoding=None, errors=None)
            basename = file_location
        log.info(payload)

        access_str = "changes/"
        result = self.post(access_str, data=payload)[1]
        log.info(result["id"])
        changeid = result["id"]

        my_file = open(filename)
        my_file_size = os.stat(filename)
        headers = {"Content-Type": "text/plain", "Content-length": "{}".format(my_file_size)}
        self.r.headers.update(headers)
        access_str = "changes/{}/edit/{}".format(changeid, basename)
        payload = my_file
        result = self.put(access_str, data=payload)
        log.info(result)

        access_str = "changes/{}/edit:publish".format(changeid)
        headers = {"Content-Type": "application/json; charset=UTF-8"}
        self.r.headers.update(headers)
        payload = json.dumps(
            {
                "notify": "NONE",
            }
        )
        result = self.post(access_str, data=payload)
        return result
        ##############################################################

    def add_info_job(self, fqdn, gerrit_project, jjbrepo, reviewid, issue_id, **kwargs):
        """Add an INFO job for a new Project.

        Adds info verify jenkins job for project.
        result['id'] can be used to ammend a review
        so that multiple projects can have info jobs added
        in a single review

        Example:

        fqdn gerrit.o-ran-sc.org
        gerrit_project test/test1
        jjbrepo ci-mangement
        """
        ###############################################################
        # Setup
        signed_off_by = config.get_setting(fqdn, "sob")
        gerrit_project_dashed = gerrit_project.replace("/", "-")
        filename = "{}.yaml".format(gerrit_project_dashed)

        if not reviewid:
            payload = self.create_change(filename, jjbrepo, issue_id, signed_off_by)
            log.info(payload)
            access_str = "changes/"
            result = self.post(access_str, data=payload)[1]
            log.info(result)
            log.info(result["id"])
            changeid = result["id"]
        else:
            changeid = reviewid

        if fqdn == "gerrit.o-ran-sc.org":
            buildnode = "centos7-builder-1c-1g"
        elif fqdn == "gerrit.onap.org":
            buildnode = "centos8-builder-2c-1g"
        else:
            buildnode = "centos7-builder-2c-1g"

        my_inline_file = """---
- project:
    name: {0}-project-view
    project-name: {0}
    views:
      - project-view\n
- project:
    name: {0}-info
    project: {1}
    project-name: {0}
    build-node: {2}
    jobs:
      - gerrit-info-yaml-verify\n""".format(
            gerrit_project_dashed, gerrit_project, buildnode
        )
        my_inline_file_size = len(my_inline_file.encode("utf-8"))
        headers = {"Content-Type": "text/plain", "Content-length": "{}".format(my_inline_file_size)}
        self.r.headers.update(headers)
        access_str = "changes/{0}/edit/jjb%2F{1}%2F{1}.yaml".format(changeid, gerrit_project_dashed)
        payload = my_inline_file
        log.info(access_str)
        result = self.put(access_str, data=payload)
        log.info(result)

        access_str = "changes/{}/edit:publish".format(changeid)
        headers = {"Content-Type": "application/json; charset=UTF-8"}
        self.r.headers.update(headers)
        payload = json.dumps(
            {
                "notify": "NONE",
            }
        )
        result = self.post(access_str, data=payload)
        log.info(result)
        return result

    def vote_on_change(self, fqdn, gerrit_project, changeid, **kwargs):
        """Helper that votes on a change.

        POST /changes/{change-id}/revisions/{revision-id}/review
        """
        log.info(fqdn, gerrit_project, changeid)
        access_str = "changes/{}/revisions/2/review".format(changeid)
        headers = {"Content-Type": "application/json; charset=UTF-8"}
        self.r.headers.update(headers)
        payload = json.dumps(
            {
                "tag": "automation",
                "message": "Vote on file",
                "labels": {
                    "Verified": +1,
                    "Code-Review": +2,
                },
            }
        )

        result = self.post(access_str, data=payload)
        # Code for projects that don't allow self merge.
        if config.get_setting(self.fqdn + ".second"):
            second_username = config.get_setting(self.fqdn + ".second", "username")
            second_password = config.get_setting(self.fqdn + ".second", "password")
            self.r.auth = (second_username, second_password)
            result = self.post(access_str, data=payload)
            self.r.auth = (self.username, self.password)
        return result

    def submit_change(self, fqdn, gerrit_project, changeid, payload, **kwargs):
        """Method so submit a change."""
        # submit a change id
        access_str = "changes/{}/submit".format(changeid)
        log.info(access_str)
        headers = {"Content-Type": "application/json; charset=UTF-8"}
        self.r.headers.update(headers)
        result = self.post(access_str, data=payload)
        return result

    def abandon_changes(self, fqdn, gerrit_project, **kwargs):
        """."""
        gerrit_project_encoded = urllib.parse.quote(gerrit_project, safe="", encoding=None, errors=None)
        access_str = "changes/?q=project:{}".format(gerrit_project_encoded)
        log.info(access_str)
        headers = {"Content-Type": "application/json; charset=UTF-8"}
        self.r.headers.update(headers)
        result = self.get(access_str)[1]
        payload = {"message": "Abandoned by automation"}
        for id in result:
            if (id["status"]) == "NEW":
                id = id["id"]
                access_str = "changes/{}/abandon".format(id)
                log.info(access_str)
                result = self.post(access_str, data=payload)[1]
                return result

    def create_change(self, filename, gerrit_project, issue_id, signed_off_by, **kwargs):
        """Method to create a gerrit change."""
        if issue_id:
            subject = "Automation adds {0}\n\nIssue-ID: {1}\n\nSigned-off-by: {2}".format(
                filename, issue_id, signed_off_by
            )
        else:
            subject = "Automation adds {0}\n\nSigned-off-by: {1}".format(filename, signed_off_by)
        payload = json.dumps(
            {
                "project": "{}".format(gerrit_project),
                "subject": "{}".format(subject),
                "branch": "master",
            }
        )
        return payload

    def sanity_check(self, fqdn, gerrit_project, **kwargs):
        """Perform a sanity check."""
        # Sanity check
        gerrit_project_encoded = urllib.parse.quote(gerrit_project, safe="", encoding=None, errors=None)
        mylist = ["projects/", "projects/{}".format(gerrit_project_encoded)]
        for access_str in mylist:
            log.info(access_str)
            try:
                result = self.get(access_str)[1]
            except Exception:
                log.info("Not found {}".format(access_str))
                exit(1)
            log.info("found {} {}".format(access_str, mylist))
        return result

    def add_git_review(self, fqdn, gerrit_project, issue_id, **kwargs):
        """Add and Submit a .gitreview for a project.

        Example:

        fqdn gerrit.o-ran-sc.org
        gerrit_project test/test1
        issue_id: CIMAN-33
        """
        signed_off_by = config.get_setting(fqdn, "sob")
        self.sanity_check(fqdn, gerrit_project)

        ###############################################################
        # Create A change set.
        filename = ".gitreview"
        payload = self.create_change(filename, gerrit_project, issue_id, signed_off_by)
        log.info(payload)

        access_str = "changes/"
        result = self.post(access_str, data=payload)[1]
        log.info(result)
        changeid = result["id"]

        ###############################################################
        # Add a file to a change set.
        my_inline_file = """
        [gerrit]
        host={0}
        port=29418
        project={1}
        defaultbranch=master
        """.format(
            fqdn, gerrit_project
        )
        my_inline_file_size = len(my_inline_file.encode("utf-8"))
        headers = {"Content-Type": "text/plain", "Content-length": "{}".format(my_inline_file_size)}
        self.r.headers.update(headers)
        access_str = "changes/{}/edit/{}".format(changeid, filename)
        payload = my_inline_file
        result = self.put(access_str, data=payload)

        if result.status_code == 409:
            log.info(result)
            log.info("Conflict detected exiting")
            exit(0)

        else:
            access_str = "changes/{}/edit:publish".format(changeid)
            headers = {"Content-Type": "application/json; charset=UTF-8"}
            self.r.headers.update(headers)
            payload = json.dumps(
                {
                    "notify": "NONE",
                }
            )
            result = self.post(access_str, data=payload)
            log.info(result)

            result = self.vote_on_change(fqdn, gerrit_project, changeid)
            log.info(result)

            time.sleep(5)
            result = self.submit_change(fqdn, gerrit_project, changeid, payload)
            log.info(result)

    def create_saml_group(self, fqdn, ldap_group, **kwargs):
        """Create saml group from ldap group."""
        ###############################################################
        payload = json.dumps({"visible_to_all": "false"})
        saml_group = "saml/{}".format(ldap_group)
        saml_group_encoded = urllib.parse.quote(saml_group, safe="", encoding=None, errors=None)
        access_str = "groups/{}".format(saml_group_encoded)
        log.info("Encoded SAML group name: {}".format(saml_group_encoded))
        result = self.put(access_str, data=payload)
        return result

    def add_github_rights(self, fqdn, gerrit_project, **kwargs):
        """Grant github read to a project."""
        ###############################################################
        # Github Rights

        gerrit_project_encoded = urllib.parse.quote(gerrit_project, safe="", encoding=None, errors=None)
        # GET /groups/?m=test%2F HTTP/1.0
        access_str = "groups/?m=GitHub%20Replication"
        log.info(access_str)
        result = self.get(access_str)[1]
        time.sleep(5)
        githubid = result["GitHub Replication"]["id"]
        log.info(githubid)

        # POST /projects/MyProject/access HTTP/1.0
        if githubid:
            payload = json.dumps(
                {
                    "add": {
                        "refs/*": {
                            "permissions": {
                                "read": {"rules": {"{}".format(githubid): {"action": "{}".format("ALLOW")}}}
                            }
                        }
                    }
                }
            )
            access_str = "projects/{}/access".format(gerrit_project_encoded)
            result = self.post(access_str, data=payload)[1]
            pretty = json.dumps(result, indent=4, sort_keys=True)
            log.info(pretty)
        else:
            log.info("Error no githubid found")

    def create_project(self, fqdn, gerrit_project, ldap_group, description, check):
        """Create a project via the gerrit API.

        Creates a gerrit project.
        Converts ldap group to saml group and sets as owner.

        Example:

        gerrit_url gerrit.o-ran-sc.org/r
        gerrit_project test/test1
        ldap_group oran-gerrit-test-test1-committers
        --description="This is a demo project"

        """
        gerrit_project = urllib.parse.quote(gerrit_project, safe="", encoding=None, errors=None)

        access_str = "projects/?query=name:{}".format(gerrit_project)
        result = self.get(access_str)[0]
        jsonText = result.text.replace(")]}'\n", "").strip()

        try:
            resultsDict = json.loads(jsonText)
        except json.decoder.JSONDecodeError:
            log.info(result)
            log.info("A problem was encountered while querying the Gerrit API.")
            log.debug(result.text)
            exit(result.status_code)

        if resultsDict:
            log.info("Project already exists")
            exit(1)
        if check:
            exit(0)

        saml_group = "saml/{}".format(ldap_group)
        log.info("SAML group name: {}".format(saml_group))

        access_str = "projects/{}".format(gerrit_project)
        payload = json.dumps(
            {
                "description": "{}".format(description),
                "submit_type": "INHERIT",
                "create_empty_commit": "True",
                "owners": ["{}".format(saml_group)],
            }
        )

        log.info(payload)
        result = self.put(access_str, data=payload)
        return result

    def list_project_permissions(self, project):
        """List a projects owners."""
        result = self.get("access/?project={}".format(project))[1][project]["local"]
        group_list = []
        for k, v in result.items():
            for kk, vv in result[k]["permissions"]["owner"]["rules"].items():
                group_list.append(kk.replace("ldap:cn=", "").replace(",ou=Groups,dc=freestandards,dc=org", ""))
        return group_list

    def list_project_inherits_from(self, gerrit_project):
        """List who a project inherits from."""
        gerrit_project = urllib.parse.quote(gerrit_project, safe="", encoding=None, errors=None)
        result = self.get("projects/{}/access".format(gerrit_project))[1]
        inherits = result["inherits_from"]["id"]
        return inherits
