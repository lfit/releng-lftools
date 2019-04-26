# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Jira api tools."""

from __future__ import print_function

import click
import requests
import json
from lftools import config



@click.group()
@click.pass_context
def jira(ctx):
    """Jira api tools."""
    pass


@click.command(name='get-scheme')
@click.argument('jiraurl')
@click.argument('endpoint')
@click.pass_context
def get_scheme(ctx, jiraurl, endpoint):
    """Get scheme ids for Jira Project creation.

    \b
    url = jira.foo.com
    endpoint is one of:
    role
    avatar/project/system
    issuesecurityschemes
    notificationscheme
    permissionscheme
    projectCategory
    """
    userAndPass = config.get_setting("jira", "base64")
    url = ("https://{}/rest/api/2/{}").format(jiraurl, endpoint)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        'Authorization' : 'Basic %s' %  userAndPass
    }
    response = requests.request(
        "GET",
        url,
        headers=headers
    )
    print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))

@click.command(name='create-project')
@click.argument('notificationscheme')
@click.argument('lead')
@click.argument('url')
@click.argument('projecttemplatekey')
@click.argument('avatarid')
@click.argument('longname')
@click.argument('shortkey')
@click.pass_context
def create_project(ctx, notificationscheme, lead, url, projecttemplatekey, avatarid, longname, shortkey):
    """

    \b
    "projectTemplateKey":  must match projectTypeKey (software)
    Valid values:
    com.pyxis.greenhopper.jira:gh-scrum-template
    com.pyxis.greenhopper.jira:gh-kanban-template
    com.pyxis.greenhopper.jira:basic-software-development-template
    optional TODO add these as options?
      "issueSecurityScheme": 10001,
      "categoryId": 10120
    Example:
    lftools jira create-project 10000 agardner jira.opnfv.org com.pyxis.greenhopper.jira:gh-scrum-template 11311 "aric test project" ARICTEST


    """
    userAndPass = config.get_setting("jira", "base64")
    url = ("https://{}/rest/api/2/project/").format(url)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        'Authorization' : 'Basic %s' %  userAndPass
    }

    payload = json.dumps({
        "notificationScheme": "{}".format(notificationscheme), #10000
        "description": "Testing api project creation",
        "lead": "{}".format(lead),
        "url": "{}".format(url),
        "projectTemplateKey": "{}".format(projecttemplatekey),
        "avatarId": "{}".format(avatarid), #11311
        "name": "{}".format(longname), #80 chars
        "permissionScheme": 0,
        "assigneeType": "PROJECT_LEAD",
        "projectTypeKey": "software",
        "key": "{}".format(shortkey), #10 chars
    })


    print(payload)
    response = requests.request(
        "POST",
        url,
        data=payload,
        headers=headers
    )

    print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))

@click.command(name='set-owner')
@click.argument('jiraurl')
@click.argument('currentgroup')
@click.argument('projectkey')
@click.argument('role')
@click.pass_context
def set_owner(ctx, jiraurl, currentgroup, projectkey, role):
    """

    \b
    Example: jira.opnfv.org opnfv-gerrit-apex-committers APEX 1002
    find admin role with lftools jira get-scheme jira.opnfv.org role
    """
    userAndPass = config.get_setting("jira", "base64")
    url = ("https://{}/rest/api/2/project/{}/role/{}").format(jiraurl, projectkey, role)

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        'Authorization' : 'Basic %s' %  userAndPass
    }

    payload = json.dumps({
        "group": [
            "{}".format(currentgroup)
        ]})

    response = requests.request(
        "POST",
        url,
        data=payload,
        headers=headers
        )

    print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))

jira.add_command(get_scheme)
jira.add_command(create_project)
jira.add_command(set_owner)
