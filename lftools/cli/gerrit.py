#!/usr/bin/env python3
# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2018 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Create a gerrit project."""

from __future__ import print_function

import json
import os
import subprocess
import sys
import time
import urllib

import click
from pygerrit2 import GerritRestAPI
from pygerrit2 import HTTPBasicAuth

from lftools import config


@click.group()
@click.pass_context
def gerrit_cli(ctx):
    """GERRIT TOOLS."""
    pass


@click.command(name='addinfofile')
@click.argument('gerrit_url')
@click.argument('gerrit_project')
@click.argument('info_file')
@click.pass_context
def addinfofile(ctx, gerrit_url, gerrit_project, info_file):
    """Add an INFO file for review to a Project.

    Requires gerrit directory.

    Example:

    gerrit_url gerrit.o-ran-sc.org/r
    gerrit_project test/test1
    """
    # Setup
    gerritfqdn = gerrit_url.split("/")[0]
    if config.has_section("gerrit"):
        user = config.get_setting("gerrit", "username")
        pass1 = config.get_setting("gerrit", "password")
        signed_off_by = config.get_setting("gerrit", "signed_off_by")
    else:
        user = config.get_setting(gerritfqdn, "username")
        pass1 = config.get_setting(gerritfqdn, "password")
        signed_off_by = config.get_setting(gerritfqdn, "signed_off_by")
    auth = HTTPBasicAuth(user, pass1)
    url = ("https://{}".format(gerrit_url))
    rest = GerritRestAPI(url=url, auth=auth)
    headers = {'Content-Type': 'application/json; charset=UTF-8'}

    ###############################################################
    # INFO.yaml
    # 'POST /changes/'

    if gerritfqdn == "gerrit.onap.org":
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
    result = rest.post(access_str, headers=headers, data=payload)
    print(result)
    print(result['id'])
    changeid = (result['id'])
    # 'PUT /changes/{change-id}/edit/path%2fto%2ffile
    my_info_file = open(info_file)
    my_info_file_size = os.stat(info_file)
    headers = {'Content-Type': 'text/plain',
               'Content-length': '{}'.format(my_info_file_size)}
    access_str = 'changes/{}/edit/INFO.yaml'.format(changeid)
    payload = my_info_file
    time.sleep(2)
    result = rest.put(access_str, headers=headers, data=payload)
    print(result)
    # 'POST /changes/{change-id}/edit:publish
    access_str = 'changes/{}/edit:publish'.format(changeid)
    headers = {'Content-Type': 'application/json; charset=UTF-8'}
    payload = json.dumps({
        "notify": "NONE",
        })
    time.sleep(2)
    result = rest.post(access_str, headers=headers, data=payload)
    print(result)
    ###############################################################


@click.command(name='addinfojob')
@click.argument('gerrit_url')
@click.argument('gerrit_project')
@click.argument('jjbrepo')
@click.option('--reviewid', type=str, required=False,
              help='ammend a review rather than making a new one')
@click.pass_context
def addinfojob(ctx, gerrit_url, gerrit_project, jjbrepo, reviewid):
    """Add an INFO job for a new Project.

    Adds info verify jenkins job for project.
    result['id'] can be used to ammend a review
    so that multiple projects can have info jobs added
    in a single review

    Example:

    gerrit_url gerrit.o-ran-sc.org/r
    gerrit_project test/test1
    jjbrepo ci-mangement
    """
    ###############################################################
    # Setup
    gerritfqdn = gerrit_url.split("/")[0]
    if config.has_section("gerrit"):
        user = config.get_setting("gerrit", "username")
        pass1 = config.get_setting("gerrit", "password")
        signed_off_by = config.get_setting("gerrit", "signed_off_by")
    else:
        user = config.get_setting(gerritfqdn, "username")
        pass1 = config.get_setting(gerritfqdn, "password")
        signed_off_by = config.get_setting(gerritfqdn, "signed_off_by")
    auth = HTTPBasicAuth(user, pass1)
    url = ("https://{}".format(gerrit_url))
    rest = GerritRestAPI(url=url, auth=auth)
    headers = {'Content-Type': 'application/json; charset=UTF-8'}
    gerrit_project_dashed = gerrit_project.replace("/", "-")
    gerrit_project_encoded = gerrit_project.replace("/", "%2F")

    ###############################################################
    # .gitreview
    # 'POST /changes/'
    if not reviewid:
        if gerritfqdn == "gerrit.onap.org":
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
        result = rest.post(access_str, headers=headers, data=payload)
        print(result)
        print(result['id'])
        changeid = (result['id'])
    else:
        changeid = (reviewid)
    # 'PUT /changes/{change-id}/edit/path%2fto%2ffile
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
    access_str = 'changes/{0}/edit/jjb%2F{1}%2Finfo-{2}.yaml'.format(
            changeid, gerrit_project_encoded, gerrit_project_dashed)
    payload = my_inline_file
    result = rest.put(access_str, headers=headers, data=payload)
    print(result)
    # 'POST /changes/{change-id}/edit:publish
    if not reviewid:
        access_str = 'changes/{}/edit:publish'.format(changeid)
        headers = {'Content-Type': 'application/json; charset=UTF-8'}
        payload = json.dumps({
            "notify": "NONE",
            })
        result = rest.post(access_str, headers=headers, data=payload)
        print(result)


@click.command(name='prepareproject')
@click.argument('gerrit_url')
@click.argument('gerrit_project')
@click.argument('info_file')
@click.pass_context
def prepareproject(ctx, gerrit_url, gerrit_project, info_file):
    """Prepare a newly created project.

    Newly created project is given a .gitreview.
    Github group is given read
    INFO.yaml is submitted for review.

    Example:

    gerrit_url gerrit.o-ran-sc.org/r
    gerrit_project test/test1
    TODO: prolog rule that dissalows self submit
    """
    ###############################################################
    # Setup
    gerritfqdn = gerrit_url.split("/")[0]

    if config.has_section("gerrit"):
        user = config.get_setting("gerrit", "username")
        pass1 = config.get_setting("gerrit", "password")
        signed_off_by = config.get_setting("gerrit", "signed_off_by")
    else:
        user = config.get_setting(gerritfqdn, "username")
        pass1 = config.get_setting(gerritfqdn, "password")
        signed_off_by = config.get_setting(gerritfqdn, "signed_off_by")

    auth = HTTPBasicAuth(user, pass1)
    url = ("https://{}".format(gerrit_url))
    rest = GerritRestAPI(url=url, auth=auth)
    headers = {'Content-Type': 'application/json; charset=UTF-8'}
    gerrit_project_encoded = urllib.parse.quote(gerrit_project, safe='', encoding=None, errors=None)

    ###############################################################
    # Sanity check
    mylist = ['projects/', 'projects/{}'.format(gerrit_project_encoded)]
    for access_str in mylist:
        try:
            result = rest.get(access_str, headers=headers)
        except:
            print("Not found {}{}".format(url, access_str))
            sys.exit(1)
        print("found {}{}".format(url, access_str))

    ###############################################################
    # .gitreview
    # 'POST /changes/'
    print(gerritfqdn)
    if gerritfqdn == "gerrit.onap.org":
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
    result = rest.post(access_str, headers=headers, data=payload)
    print(result)
    print(result['id'])
    changeid = (result['id'])
    # 'PUT /changes/{change-id}/edit/path%2fto%2ffile
    my_inline_file = """
    [gerrit]
    host={0}
    port=29418
    project={1}
    defaultbranch=master
    """.format(gerritfqdn, gerrit_project)
    my_inline_file_size = len(my_inline_file.encode('utf-8'))
    headers = {'Content-Type': 'text/plain',
               'Content-length': '{}'.format(my_inline_file_size)}
    access_str = 'changes/{}/edit/.gitreview'.format(changeid)
    payload = my_inline_file
    result = rest.put(access_str, headers=headers, data=payload)
    time.sleep(5)
    print(result)
    # 'POST /changes/{change-id}/edit:publish
    access_str = 'changes/{}/edit:publish'.format(changeid)
    headers = {'Content-Type': 'application/json; charset=UTF-8'}
    payload = json.dumps({
        "notify": "NONE",
        })
    result = rest.post(access_str, headers=headers, data=payload)
    time.sleep(5)
    print(result)
    """POST /changes/{change-id}/revisions/{revision-id}/review"""
    access_str = 'changes/{}/revisions/2/review'.format(changeid)
    headers = {'Content-Type': 'application/json; charset=UTF-8'}
    payload = json.dumps({
        "tag": "automation",
        "message": "Vote on gitreview",
        "labels": {
            "Verified": +1,
            "Code-Review": +2,
        }
        })
    result = rest.post(access_str, headers=headers, data=payload)
    time.sleep(5)
    print(result)
    """POST /changes/{change-id}/submit"""
    access_str = 'changes/{}/submit'.format(changeid)
    headers = {'Content-Type': 'application/json; charset=UTF-8'}
    result = rest.post(access_str, headers=headers, data=payload)
    time.sleep(5)
    print(result)

    ###############################################################
    # Github Rights

    # GET /groups/?m=test%2F HTTP/1.0
    access_str = 'groups/?m=GitHub%20Replication'
    print(access_str)
    result = rest.get(access_str, headers=headers)
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
    result = rest.post(access_str, headers=headers, data=payload)
    time.sleep(5)
    pretty = json.dumps(result, indent=4, sort_keys=True)
    print(pretty)

    ###############################################################
    # INFO.yaml
    # 'POST /changes/'

    if gerritfqdn == "gerrit.onap.org":
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
    result = rest.post(access_str, headers=headers, data=payload)
    time.sleep(5)
    print(result)
    print(result['id'])
    changeid = (result['id'])
    # 'PUT /changes/{change-id}/edit/path%2fto%2ffile
    my_inline_file = open(info_file)
    my_inline_file_size = os.stat(info_file)
    headers = {'Content-Type': 'text/plain',
               'Content-length': '{}'.format(my_inline_file_size)}
    access_str = 'changes/{}/edit/INFO.yaml'.format(changeid)
    payload = my_inline_file
    result = rest.put(access_str, headers=headers, data=payload)
    time.sleep(5)
    print(result)
    # 'POST /changes/{change-id}/edit:publish
    access_str = 'changes/{}/edit:publish'.format(changeid)
    headers = {'Content-Type': 'application/json; charset=UTF-8'}
    payload = json.dumps({
        "notify": "NONE",
        })
    result = rest.post(access_str, headers=headers, data=payload)
    print(result)
    ###############################################################


# Creates a gerrit project if project does not exist and adds ldap group as owner.
# TODO: does not support inherited permissions from other than All-Projects.
@click.command(name='createproject')
@click.argument('gerrit_url')
@click.argument('gerrit_project')
@click.argument('ldap_group')
@click.option('--check', is_flag=True,
              help='just check if the project exists')
@click.pass_context
def createproject(ctx, gerrit_url, gerrit_project, ldap_group, check):
    """Create a project via the gerrit API.

    Creates a gerrit project.
    Sets ldap group as owner.

    Example:

    gerrit_url gerrit.o-ran-sc.org/r
    gerrit_project test/test1
    ldap_group oran-gerrit-test-test1-committers

    """
    gerritfqdn = gerrit_url.split("/")[0]
    if config.has_section("gerrit"):
        user = config.get_setting("gerrit", "username")
        pass1 = config.get_setting("gerrit", "password")
    else:
        user = config.get_setting(gerritfqdn, "username")
        pass1 = config.get_setting(gerritfqdn, "password")

    user = config.get_setting("gerrit", "username")
    pass1 = config.get_setting("gerrit", "password")
    auth = HTTPBasicAuth(user, pass1)
    url = ("https://{}".format(gerrit_url))
    rest = GerritRestAPI(url=url, auth=auth)
    headers = {'Content-Type': 'application/json; charset=UTF-8'}
    gerrit_project = urllib.parse.quote(gerrit_project, safe='', encoding=None, errors=None)

    access_str = 'projects/{}'.format(gerrit_project)
    try:
        result = rest.get(access_str, headers=headers)
        print("found {}{}".format(url, access_str))
        projectexists = True
    except:
        projectexists = False
        print("not found {}{}".format(url, access_str))

    if projectexists:
        print("Project already exists")
        sys.exit(1)
    if check:
        sys.exit(0)

    ldapgroup = "ldap:cn={},ou=Groups,dc=freestandards,dc=org".format(ldap_group)

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


@click.command(name='create')
@click.argument('gerrit_url')
@click.argument('ldap_group')
@click.argument('repo')
@click.argument('user')
@click.option('--enable', is_flag=True,
              help='Enable replication to Github.')
@click.option('--parent', type=str, required=False,
              help='Specify parent other than "All-Projects".')
@click.pass_context
def create(
        ctx, gerrit_url, ldap_group, repo, user, enable, parent):
    """Create and configure permissions for a new gerrit repo.

    OLD SSH METHOD DEPRECATED. PLEASE USE API METHOD.

    GERRIT_URL: server fqdn ex: gerrit.localhost

    LDAP_GROUP: owner ex: project-gerrit-group-committers

    REPO: repo name ex: testrepo

    USER: user that has permissions in gerrit
    """
    params = ['gerrit_create']
    params.extend(["-s", gerrit_url])
    params.extend(["-o", ldap_group])
    params.extend(["-r", repo])
    params.extend(["-u", user])
    if parent:
        params.extend(["-p", parent])
    if enable:
        params.extend(["-e"])
    status = subprocess.call(params)
    sys.exit(status)


gerrit_cli.add_command(create)
gerrit_cli.add_command(addinfojob)
gerrit_cli.add_command(addinfofile)
gerrit_cli.add_command(prepareproject)
gerrit_cli.add_command(createproject)
