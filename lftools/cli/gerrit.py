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
    url = ("https://{}/r".format(gerrit_url))
    rest = GerritRestAPI(url=url, auth=auth)
    headers = {'Content-Type': 'application/json; charset=UTF-8'}
    access_str = '/projects/'
    result = rest.get(access_str, headers=headers)

    all_projects = []
    for name, values in result.items():
        idlink = (values['id'])
        all_projects.append(idlink)
    return(all_projects)

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


#   for line in f:
#       if re.match(">",line):
#          pass
#       else:
#          line = line.rstrip("\n")
#          string = string + line


    for projectid in all_projects:
        if projectid == "All-Projects" or projectid == "All-Users":
            print("--- Skipping {} ---".format(projectid))
            pass
        if not re.search("%2F", projectid):
            print("--- Top level project Skipping {} ---".format(projectid))
            pass
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
                owner = "None"

            if owner == "None" and githubid:
                print("    Github:", owner)
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
    if dryrun:
        return("        -Dry Run not modifying {}".format(payload))
        #return(access_str, payload)
    else:
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
