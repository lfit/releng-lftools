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

import requests
import subprocess
import sys
import json
import re
import urllib
#from urllib.parse import urlparse

import click
from pygerrit2 import GerritRestAPI, HTTPBasicAuth
from requests.utils import get_netrc_auth
from lftools import config


@click.group()
@click.pass_context
def gerrit_cli(ctx):
    """GERRIT TOOLS."""
    pass


# Helper to list all projects.
def listprojects(gerrit_url):
    user = config.get_setting("gerrit", "username")
    pass1 = config.get_setting("gerrit", "password")
    auth = HTTPBasicAuth(user, pass1)
    url = ("https://{}".format(gerrit_url))
    rest = GerritRestAPI(url=url, auth=auth)
    headers = {'Content-Type': 'application/json; charset=UTF-8'}
    access_str = '/projects/'
    result = rest.get(access_str, headers=headers)

    all_projects = []
    for name, values in result.items():
        idlink = (values['id'])
        state = (values['state'])
        if state == "ACTIVE":
            all_projects.append(idlink)
    return(all_projects)



#This actually creates a change and then post a gitreview
@click.command(name='checkproject')
@click.argument('gerrit_url')
@click.argument('gerrit_project')
@click.pass_context
def checkproject(ctx, gerrit_url, gerrit_project):
    user = config.get_setting("gerrit", "username")
    pass1 = config.get_setting("gerrit", "password")
    auth = HTTPBasicAuth(user, pass1)
    url = ("https://{}".format(gerrit_url))
    rest = GerritRestAPI(url=url, auth=auth)
    headers = {'Content-Type': 'application/json; charset=UTF-8'}
    gerritfqdn = gerrit_url.split("/")[0]
    signed_off_by = "Aric Gardner <agardner@linuxfoundation.org>"


    gerrit_project_encoded = urllib.parse.quote(gerrit_project, safe='', encoding=None, errors=None)
    mylist = ['projects/', 'projects/{}'.format(gerrit_project_encoded)]
    #check if gerrit exists, check if project exists
    for access_str in mylist:
        try:
            result = rest.get(access_str, headers=headers)
        except:
            print("Not found {}{}".format(url, access_str))
            sys.exit(1)
        print("found {}{}".format(url, access_str))

    # 'POST /changes/'
    payload = json.dumps({
        "project" : '{}'.format(gerrit_project),
        "subject" : 'Automation adds Gitreview\n\nSigned-off-by: {}'.format(signed_off_by),
        "branch" : 'master',
        })
 
    
    print(payload)
    access_str = 'changes/'
    result = rest.post(access_str, headers=headers, data=payload)
    print(result)
    print(result['id'])
    changeid = (result['id'])

    #'PUT /changes/{change-id}/edit/path%2fto%2ffile
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
    print(result)

    #'POST /changes/{change-id}/edit:publish
    access_str = 'changes/{}/edit:publish'.format(changeid)
    headers = {'Content-Type': 'application/json; charset=UTF-8'}
    payload = json.dumps({
        "notify" : "NONE",
        })
    result = rest.post(access_str, headers=headers, data=payload)
    print(result)

    #'POST /changes/{change-id}/revisions/{revision-id}/review'
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
    print(result)

    #'POST /changes/{change-id}/submit'
    access_str = 'changes/{}/submit'.format(changeid)
    headers = {'Content-Type': 'application/json; charset=UTF-8'}
    result = rest.post(access_str, headers=headers, data=payload)
    print(result)


@click.command(name='createproject')
@click.argument('gerrit_url')
@click.argument('gerrit_project')
@click.argument('ldap_group')
@click.pass_context
def createproject(ctx, gerrit_url, gerrit_project, ldap_group):
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

    else:
        ldapgroup = "ldap:cn={},ou=Groups,dc=freestandards,dc=org".format(ldap_group)

        access_str = 'projects/{}'.format(gerrit_project)
        payload = json.dumps({
            "description": "This is a demo project.",
            "submit_type": "INHERIT",
            "create_empty_commit" : "True",
            "owners": [
                "{}".format(ldapgroup)
                ]
        })

        print(payload)
        result = rest.put(access_str, headers=headers, data=payload)
        print(result)
        
@click.command(name='fixaccessrights')
@click.option('--projectid', type=str, required=False,
              help='Check only one project')
@click.argument('gerrit_url')
@click.option('--githubid', type=str, required=False,
              help='daebbf523be390041a1a9c0e340a6d833aae5043')
@click.option('--dryrun', is_flag=True,
              help='show post, but dont post')
@click.pass_context
def fixaccessrights(ctx, projectid, gerrit_url, githubid, dryrun):
    user = config.get_setting("gerrit", "username")
    pass1 = config.get_setting("gerrit", "password")
    auth = HTTPBasicAuth(user, pass1)
    url = ("https://{}/r".format(gerrit_url))
    rest = GerritRestAPI(url=url, auth=auth)
    headers = {'Content-Type': 'application/json; charset=UTF-8'}
    all_projects = []

    #If a projectid is passed dont generate a list of projects from list projects
    if projectid:
        all_projects.append(projectid)
    else: 
        all_projects = listprojects(gerrit_url=gerrit_url)

    for projectid in all_projects:
        #if projectid == "All-Projects" or projectid == "All-Users":
        #    print("--- Skipping {} ---".format(projectid))
        if not re.search("%2F", projectid):
            print("--- Skipping Top level project {} ---".format(projectid))
        else:
            access_str = 'projects/{}/access'.format(projectid)
            result = rest.get(access_str, headers=headers)
            print("Project:", projectid)

            if 'inherits_from' in result:
                inherits = (result['inherits_from']['id'])
                print("    Inherits from:", inherits)
                if inherits != "All-Projects":
                    output = accessrights(projectid=projectid,
                                          gerrit_url=gerrit_url,
                                          setparent=True,
                                          setowner=False,
                                          githubid=False,
                                          dryrun=dryrun)

                    print(output)
            else:
                print("no key")

            try:
                owner = (result['local']['refs/*']['permissions']['owner']['rules'])
            except KeyError:
                owner = "None"

            if owner == "None":
                print("    Owner:", owner)
                output = accessrights(projectid=projectid,
                                      gerrit_url=gerrit_url,
                                      setparent=False,
                                      setowner=True,
                                      githubid=False,
                                      dryrun=dryrun)
                print(output)

            else:
                for name in owner.keys():
                    print("    Owner:", name)


            try:
                github = (result['local']['refs/*']['permissions']['read']['rules'])
            except KeyError:
                github = "None"

            if github == "None" and githubid:
                print("    Github:", github)
                output = accessrights(projectid=projectid,
                                      gerrit_url=gerrit_url,
                                      setparent=False,
                                      setowner=False,
                                      githubid=githubid,
                                      dryrun=dryrun)
                print(output)
            else:
                for name in github.keys():
                    print("    Github:", name)

def accessrights(projectid, gerrit_url, setparent, setowner, githubid, dryrun):
    user = config.get_setting("gerrit", "username")
    pass1 = config.get_setting("gerrit", "password")
    auth = HTTPBasicAuth(user, pass1)
    url = ("https://{}/r".format(gerrit_url))
    rest = GerritRestAPI(url=url, auth=auth)

    #print("This is Project ID:", projectid)
    project_dashed = projectid.replace("%2F", "-")
    headers = {'Content-Type': 'application/json; charset=UTF-8'}

    if githubid:
        payload = json.dumps({
            "add": {
                "refs/*": {
                    "permissions": {
                        "read": {
                            "rules": {
                                "{}".format(githubid) : {
                                    "action": "{}".format("ALLOW")
        }}}}}}
        })

    if setparent:
        payload = json.dumps({
            "parent": "All-Projects"
        })

    if setowner:
        payload = json.dumps({
            "add": {
                "refs/*": {
                    "permissions": {
                        "owner": {
                            "rules": {
                                "ldap:cn=onap-gerrit-{}-committers,ou=Groups,dc=freestandards,dc=org".format(project_dashed): {
                                    "action": "ALLOW",
                                    "force": "false"
            }}}}}}
        })



    access_str = 'projects/{}/access'.format(projectid)

    if dryrun:
        return("        -Dry Run not modifying {}".format(payload))
    else:
        print("not doing this")

        result = rest.post(access_str, headers=headers, data=payload)
        pretty = json.dumps(result, indent=4, sort_keys=True)
        return(pretty)

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
gerrit_cli.add_command(fixaccessrights)
gerrit_cli.add_command(checkproject)
gerrit_cli.add_command(createproject)
