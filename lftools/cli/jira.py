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

import json

import click
import requests

from lftools import config


@click.group()
@click.pass_context
def jira(ctx):
    """Jira api tools."""
    pass


@click.command(name='get')
@click.argument('jiraurl')
@click.argument('endpoint')
@click.pass_context
def get_scheme(ctx, jiraurl, endpoint):
    """Get a jira's api end point.

    \b
    url = jira.foo.com
    Endpoints I have used so far:
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
        "Authorization": "Basic %s" % userAndPass
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
@click.argument('longname')
@click.argument('shortkey')
@click.argument('projecturl')
@click.pass_context
def create_project(ctx, notificationscheme, lead, url, projecttemplatekey, longname, shortkey, projecturl):
    """Create a JIRA project.

    \b
    notificationscheme: 10000 is the global default
    lead: lfid of the project lead. (lead must have previously signed in to jira)
    url: jira.yourproject.org
    projectTemplateKey: Valid values are one of the following
    com.pyxis.greenhopper.jira:gh-scrum-template
    com.pyxis.greenhopper.jira:gh-kanban-template
    com.pyxis.greenhopper.jira:basic-software-development-template
    longname: Long project name, please double quote.
    shortkey: Ten character SHORTKEY must be capitolized
    projecturl: Projects URL, probaly a link to their wiki.

    TODO do we need to add these as options?
    issueSecurityScheme: 10001,
    categoryId: 10120

    Example:
    lftools jira create-project 10000 agardner jira.opnfv.org com.pyxis.greenhopper.jira:gh-scrum-template "Aric test project" ARICTEST https://wiki.opnfv.org/aric
    """
    userAndPass = config.get_setting("jira", "base64")
    url = ("https://{}/rest/api/2/project/").format(url)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Basic %s" % userAndPass
    }

    payload = json.dumps({
        "notificationScheme": "{}".format(notificationscheme),  # 10000 make a default
        "description": "Testing api project creation",
        "lead": "{}".format(lead),
        "url": "{}".format(projecturl),
        "projectTemplateKey": "{}".format(projecttemplatekey),
        "name": "{}".format(longname),  # 80 chars
        "permissionScheme": 0,  # this is default
        "assigneeType": "PROJECT_LEAD",
        "projectTypeKey": "software",
        "key": "{}".format(shortkey),  # 10 chars
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
    """Set an ldap group as owner on a jira project. 1002 is the role for owner, 1001 is devloper.

    \b
    Example: jira.opnfv.org opnfv-gerrit-apex-committers APEX 1002
    Rolls may be diffrent across jiras.
    find admin role with lftools jira get-scheme jira.opnfv.org role
    """
    userAndPass = config.get_setting("jira", "base64")
    url = ("https://{}/rest/api/2/project/{}/role/{}").format(jiraurl, projectkey, role)

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Basic %s" % userAndPass
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
