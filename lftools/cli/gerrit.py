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

import click
#from pygerrit2 import GerritRestAPI, HTTPBasicAuthFromNetrc
from pygerrit2 import GerritRestAPI, HTTPBasicAuth
from requests.utils import get_netrc_auth
from lftools import config


@click.group()
@click.pass_context
def gerrit_cli(ctx):
    """GERRIT TOOLS."""
    pass

#@click.command(name='listprojects')
#@click.argument('gerrit_url')
#@click.option('--ids', is_flag=True,
#              help='only show ids')
#@click.pass_context

def listprojects(gerrit_url, ids):
    user = config.get_setting("gerrit", "username")
    pass1 = config.get_setting("gerrit", "password")
    auth = HTTPBasicAuth(user, pass1)
    url = ("https://{}/r".format(gerrit_url))
    rest = GerritRestAPI(url=url, auth=auth)
    headers = {'Content-Type': 'application/json; charset=UTF-8'}
    access_str = '/projects/'
    result = rest.get(access_str, headers=headers)

    all_projects = []
    if ids:
        for name, values in result.items():
            idlink = (values['id'])
            #name_dashed = name.replace("/", "-")
            #print(name, name_dashed, idlink)
            #print(name, idlink)
            all_projects.append(idlink)
    else:
        pretty = json.dumps(result, indent=4, sort_keys=True)
        print(pretty)

    return(all_projects)

@click.command(name='checkaccessrights')
@click.option('--projectid', type=str, required=False,
              help='Check only one project')
@click.argument('gerrit_url')
@click.option('--githubid', type=str, required=False,
              help='daebbf523be390041a1a9c0e340a6d833aae5043')
@click.pass_context
def checkaccessrights(ctx, projectid, gerrit_url, githubid):
    user = config.get_setting("gerrit", "username")
    pass1 = config.get_setting("gerrit", "password")
    auth = HTTPBasicAuth(user, pass1)
    url = ("https://{}/r".format(gerrit_url))
    rest = GerritRestAPI(url=url, auth=auth)
    headers = {'Content-Type': 'application/json; charset=UTF-8'}
    all_projects = []

    if projectid:
        all_projects.append(projectid)
    else: 
        all_projects = listprojects(gerrit_url=gerrit_url, ids=True)

    for projectid in all_projects:
        access_str = 'projects/{}/access'.format(projectid)
        result = rest.get(access_str, headers=headers)

        #Might be more usefull to leave un formatted
        #project = project.replace("%2F", "/")
        print("Project:", projectid)
        if 'inherits_from' in result:
            inherits = (result['inherits_from']['id'])
            print("Inherits from:", inherits)

            if inherits != "All-Projects":
                output = accessrights(projectid=projectid, gerrit_url=gerrit_url, setparent=True, setowner=False, githubid=False)
                print(output)

        else:
            print("no key")

        try:
            owner = (result['local']['refs/*']['permissions']['owner']['rules'])
        except KeyError:
            owner = "None"

        if owner == "None":
            print("Owner:", owner)
            output = accessrights(projectid=projectid, gerrit_url=gerrit_url, setparent=False, setowner=True, githubid=False)
            print(output)

        else:
            for name in owner.keys():
                print("Owner:", name)


        try:
            github = (result['local']['refs/*']['permissions']['read']['rules'])
        except KeyError:
            owner = "None"

        if owner == "None" and githubid:
            print("Github:", owner)
            output = accessrights(projectid=projectid, gerrit_url=gerrit_url, setparent=False, setowner=False, githubid=githubid)
            print(output)
        else:
            for name in github.keys():
                print("Github:", name)


#@click.command(name='accessrights')
#@click.argument('projectid')
#@click.argument('gerrit_url')
#@click.argument('gerrit_project')
#@click.argument('repo')
#@click.option('--githubid', type=str, required=False,
#              help='daebbf523be390041a1a9c0e340a6d833aae5043')
#@click.option('--deletefirst', is_flag=True,
#              help='delete all permissions before adding new ones')
#@click.option('--setparent', is_flag=True,
#              help='set parent to All-Projects')
#@click.option('--setowner', is_flag=True,
#              help='set owner to gerrit_projet')
#@click.pass_context

def accessrights(projectid, gerrit_url, setparent, setowner, githubid):
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

    #if deletefirst:
    #    payload = json.dumps({
    #        "remove": {
    #            "refs/*": {
    #        }}
    #    })
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
    return(access_str, payload)
    #result = rest.post(access_str, headers=headers, data=payload)

    #pretty = json.dumps(result, indent=4, sort_keys=True)
    #print(pretty)

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
#gerrit_cli.add_command(listprojects)
#gerrit_cli.add_command(accessrights)
gerrit_cli.add_command(checkaccessrights)
