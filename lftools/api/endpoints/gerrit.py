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
import os
import time
import urllib

from lftools import config
import lftools.api.client as client


class Gerrit(client.RestApi):
    """API endpoint wrapper for Gerrit.

    Be sure to always include the trailing "/" when adding
    new methods.
    """

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

        super(Gerrit, self).__init__(**params)

    def add_info_file(self, fqdn, gerrit_project, info_file, **kwargs):
        """Add an INFO file for review to a Project.

        Requires gerrit directory.

        Example:

        gerrit_url gerrit.o-ran-sc.org/r
        gerrit_project test/test1
        """
        # Setup
        # headers = {'Content-Type': 'application/json; charset=UTF-8'}

        ###############################################################
        # INFO.yaml
        # 'POST /changes/'

        # Need exceptions here. we should pass the ISSUE-ID like the signed off by line
        signed_off_by = config.get_setting(fqdn, 'sob')

        if fqdn == 'gerrit.onap.org':
            data = {
                'project': '{}'.format(gerrit_project),
                'subject': 'Automation adds Gitreview\n\nIssue-ID: CIMAN-33\n\nSigned-off-by: {}'.format(signed_off_by),
                'branch': 'master',
            }
        else:
            data = {
                'project': gerrit_project,
                'subject': 'My log message \n\nSigned-off-by: {}'.format(signed_off_by),
                'branch': 'master',
            }

        json_data = json.dumps(data)
        result = self.post('changes/', data=json_data)[1]

        print(result)
        print(result['id'])
        changeid = (result['id'])

        # 'PUT /changes/{change-id}/edit/path%2fto%2ffile
        my_info_file = open(info_file)
        my_info_file_size = os.stat(info_file)
        headers = {'Content-Type': 'text/plain',
                   'Content-length': '{}'.format(my_info_file_size)}
        self.r.headers.update(headers)
        access_str = 'changes/{}/edit/INFO.yaml'.format(changeid)
        payload = my_info_file
        result = self.put(access_str, data=payload)
        print(result)
        # 'POST /changes/{change-id}/edit:publish
        access_str = 'changes/{}/edit:publish'.format(changeid)
        headers = {'Content-Type': 'application/json; charset=UTF-8'}
        self.r.headers.update(headers)
        payload = json.dumps({
            "notify": "NONE",
        })
        result = self.post(access_str, data=payload)
        print(result)
        return(result)
        ##############################################################

    def add_info_job(self, fqdn, gerrit_project, jjbrepo, reviewid, **kwargs):
        """Add an INFO job for a new Project.
    
        Adds info verify jenkins job for project.
        result['id'] can be used to ammend a review
        so that multiple projects can have info jobs added
        in a single review
    
        Example:
    
        gerrit_fqdn gerrit.o-ran-sc.org
        gerrit_project test/test1
        jjbrepo ci-mangement
        """
        ###############################################################
        # Setup
        signed_off_by = config.get_setting(fqdn, 'sob')
        gerrit_project_dashed = gerrit_project.replace("/", "-")
        #gerrit_project_encoded = gerrit_project.replace("/", "%2F")
        gerrit_project_encoded = urllib.parse.quote(gerrit_project, safe='', encoding=None, errors=None)
    
        if not reviewid:
            if fqdn == "gerrit.onap.org":
                payload = json.dumps({
                    "project": '{}'.format(jjbrepo),
                    "subject": 'Automation adds INFO job\n\nIssue-ID: CIMAN-33\n\nSigned-off-by: {}'.format(signed_off_by),
                    "branch": 'master',
                    })
            else:
                payload = json.dumps({
                    "project": '{}'.format(jjbrepo),
                    "subject": 'Automation adds INFO job\n\nSigned-off-by: {}'.format(signed_off_by),
                    "branch": 'master',
                    })
    
            print(payload)
            access_str = 'changes/'
            result = self.post(access_str, data=payload)[1]
            print(result)
            print(result['id'])
            changeid = (result['id'])
        else:
            changeid = (reviewid)
        my_inline_file = """---
    - project:
        name: {0}-info
        project-name: {0}
        jobs:
          - gerrit-info-yaml-verify
        project: {1}
        branch: master\n""".format(gerrit_project_dashed, gerrit_project)
        my_inline_file_size = len(my_inline_file.encode('utf-8'))
        headers = {'Content-Type': 'text/plain',
                   'Content-length': '{}'.format(my_inline_file_size)}
        self.r.headers.update(headers)
        access_str = 'changes/{0}/edit/jjb%2F{1}%2Finfo-{2}.yaml'.format(
            changeid, gerrit_project_encoded, gerrit_project_dashed)
        payload = my_inline_file
        result = self.put(access_str, data=payload)
        print(result)
        if not reviewid:
            access_str = 'changes/{}/edit:publish'.format(changeid)
            headers = {'Content-Type': 'application/json; charset=UTF-8'}
            self.r.headers.update(headers)
            payload = json.dumps({
                "notify": "NONE",
                })
            result = self.post(access_str, data=payload)
            print(result)
        return(result)
    
    
    def prepare_project(self, fqdn, gerrit_project, info_file, **kwargs):
        """Prepare a newly created project.
    
        Newly created project is given a .gitreview.
        Github group is given read
        INFO.yaml is submitted for review.
    
        Example:
    
        gerrit_fqdn gerrit.o-ran-sc.org
        gerrit_project test/test1
        TODO: prolog rule that dissalows self submit
        """
        ###############################################################
        # Setup
        # ONAP does not allow self merges, and so we use onap-release for a 2nd +2
        #if fqdn == "gerrit.onap.org":
        #    if config.has_section("gerrit.onap.second"):
        #        uservote = config.get_setting("gerrit.onap.second", "username")
        #        passvote = config.get_setting("gerrit.onap.second", "password")
    
        #if fqdn == "gerrit.onap.org":
        #    auth_vote = HTTPBasicAuth(uservote, passvote)
        #    restvote = GerritRestAPI(url=url, auth=auth_vote)
        gerrit_project_encoded = urllib.parse.quote(gerrit_project, safe='', encoding=None, errors=None)
        signed_off_by = config.get_setting(fqdn, 'sob')
        ###############################################################

        # Sanity check
        mylist = ['projects/', 'projects/{}'.format(gerrit_project_encoded)]
        for access_str in mylist:
            print(access_str)

            try:
                result = self.get(access_str)[1]
            except:
                print("Not found {}".format(access_str))
                sys.exit(1)
            print("found {}".format(access_str))

        ###############################################################
        # .gitreview
        # 'POST /changes/'
        print(fqdn)
        if fqdn == "gerrit.onap.org":
            payload = json.dumps({
                "project": '{}'.format(gerrit_project),
                "subject": 'Automation adds Gitreview\n\nIssue-ID: CIMAN-33\n\nSigned-off-by: {}'.format(signed_off_by),
                "branch": 'master',
                })
        else:
            payload = json.dumps({
                "project": '{}'.format(gerrit_project),
                "subject": 'Automation adds Gitreview\n\nSigned-off-by: {}'.format(signed_off_by),
                "branch": 'master',
                })
    
        print(payload)
        access_str = 'changes/'
        result = self.post(access_str, data=payload)[1]
        print(result)
        print(result['id'])
        changeid = (result['id'])
        my_inline_file = """
        [gerrit]
        host={0}
        port=29418
        project={1}
        defaultbranch=master
        """.format(fqdn, gerrit_project)
        my_inline_file_size = len(my_inline_file.encode('utf-8'))
        headers = {'Content-Type': 'text/plain',
                   'Content-length': '{}'.format(my_inline_file_size)}
        self.r.headers.update(headers)
        access_str = 'changes/{}/edit/.gitreview'.format(changeid)
        payload = my_inline_file
        result = rest.put(access_str, data=payload)[1]
        print(result)
        # 'POST /changes/{change-id}/edit:publish
        access_str = 'changes/{}/edit:publish'.format(changeid)
        headers = {'Content-Type': 'application/json; charset=UTF-8'}
        self.r.headers.update(headers)
        payload = json.dumps({
            "notify": "NONE",
            })
        result = self.post(access_str, data=payload)[1]
        print(result)
        """POST /changes/{change-id}/revisions/{revision-id}/review"""
        access_str = 'changes/{}/revisions/2/review'.format(changeid)
        headers = {'Content-Type': 'application/json; charset=UTF-8'}
        self.r.headers.update(headers)
        payload = json.dumps({
            "tag": "automation",
            "message": "Vote on gitreview",
            "labels": {
                "Verified": +1,
                "Code-Review": +2,
            }
            })
        result = self.post(access_str, data=payload)
        time.sleep(5)
        # ONAP needs a second +2 from onap-release, headers and payload do not change
        #if fqdn == "gerrit.onap.org":
        #    result = restvote.post(access_str, headers=headers, data=payload)
        #    time.sleep(5)
        print(result)
    
        # We submit the .gitreview
        """POST /changes/{change-id}/submit"""
        access_str = 'changes/{}/submit'.format(changeid)
        headers = {'Content-Type': 'application/json; charset=UTF-8'}
        self.r.headers.update(headers)
        result = self.post(access_str, data=payload)[1]
        time.sleep(5)
        print(result)
    
        ###############################################################
        # Github Rights
    
        # GET /groups/?m=test%2F HTTP/1.0
        access_str = 'groups/?m=GitHub%20Replication'
        print(access_str)
        result = self.get(access_str)[1]
        time.sleep(5)
        githubid = (result['GitHub Replication']['id'])
        print(githubid)
    
        # POST /projects/MyProject/access HTTP/1.0
        if githubid:
            payload = json.dumps({
                "add": {
                    "refs/*": {
                        "permissions": {
                            "read": {
                                "rules": {
                                    "{}".format(githubid): {
                                        "action": "{}".format("ALLOW")
                                        }}}}}}
            })
        access_str = 'projects/{}/access'.format(gerrit_project_encoded)
        result = self.post(access_str, data=payload)[1]
        time.sleep(5)
        pretty = json.dumps(result, indent=4, sort_keys=True)
        print(pretty)
    
        ###############################################################
        # INFO.yaml
        # 'POST /changes/'
    
        if fqdn == "gerrit.onap.org":
            payload = json.dumps({
                "project": '{}'.format(gerrit_project),
                "subject": 'Automation adds INFO.yaml\n\nIssue-ID: CIMAN-33\n\nSigned-off-by: {}'.format(signed_off_by),
                "branch": 'master',
                })
        else:
            payload = json.dumps({
                "project": '{}'.format(gerrit_project),
                "subject": 'Automation adds INFO.yaml\n\nSigned-off-by: {}'.format(signed_off_by),
                "branch": 'master',
                })
    
        print(payload)
        access_str = 'changes/'
        result = self.post(access_str, data=payload)[1]
        time.sleep(5)
        print(result)
        print(result['id'])
        changeid = (result['id'])
        # 'PUT /changes/{change-id}/edit/path%2fto%2ffile
        my_inline_file = open(info_file)
        my_inline_file_size = os.stat(info_file)
        headers = {'Content-Type': 'text/plain',
                   'Content-length': '{}'.format(my_inline_file_size)}
        self.r.headers.update(headers)
        access_str = 'changes/{}/edit/INFO.yaml'.format(changeid)
        payload = my_inline_file
        result = self.put(access_str, data=payload)[1]
        time.sleep(5)
        print(result)
        # 'POST /changes/{change-id}/edit:publish
        access_str = 'changes/{}/edit:publish'.format(changeid)
        headers = {'Content-Type': 'application/json; charset=UTF-8'}
        self.r.headers.update(headers)
        payload = json.dumps({
            "notify": "NONE",
            })
        result = self.post(access_str, data=payload)[1]
        print(result)
        return(result)
        ###############################################################
    
    
    def create_project(self, fqdn, gerrit_project, ldap_group, check):
        """Create a project via the gerrit API.
    
        Creates a gerrit project.
        Sets ldap group as owner.
    
        Example:
    
        gerrit_url gerrit.o-ran-sc.org/r
        gerrit_project test/test1
        ldap_group oran-gerrit-test-test1-committers
    
        """
        gerrit_project = urllib.parse.quote(gerrit_project, safe='', encoding=None, errors=None)
    
        #self.r.headers.update(headers)
        access_str = 'projects/{}'.format(gerrit_project)
        try:
            result = self.get(access_str)[0]
            print(result)
            print("found {}".format(access_str))
            projectexists = True
        except:
            projectexists = False
            print("not found {}".format(access_str))
    
        if projectexists:
            print("Project already exists")
            exit(1)
        if check:
            exit(0)
    
        ldapgroup = "ldap:cn={},ou=Groups,dc=freestandards,dc=org".format(ldap_group)
        
        print(ldapgroup)
        exit(0)
    
        access_str = 'projects/{}'.format(gerrit_project)
        payload = json.dumps({
            "description": "This is a demo project.",
            "submit_type": "INHERIT",
            "create_empty_commit": "True",
            "owners": [
                "{}".format(ldapgroup)
                ]
        })
    
        print(payload)
        result = rest.put(access_str, headers=headers, data=payload)
        print(result)
        return(result)
        
