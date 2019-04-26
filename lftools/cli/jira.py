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
import logging

import click
import requests

from lftools import config

log = logging.getLogger(__name__)


@click.group()
@click.pass_context
def jira(ctx):
    """Jira api tools."""
    pass


@click.command(name='get')
@click.argument('url')
@click.argument('endpoint')
@click.pass_context
def get_scheme(ctx, url, endpoint):
    """Get request a jira end-point.

    \b
    url = jira.example.com
    Example Endpoints:
    role
    avatar/project/system
    issuesecurityschemes
    notificationscheme
    permissionscheme
    projectCategory
    """
    userandpass = config.get_setting("jira", "base64")
    url = ("https://{}/rest/api/2/{}").format(url, endpoint)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Basic %s" % userandpass
    }
    response = requests.request(
        "GET",
        url,
        headers=headers
    )
    log.info(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))


@click.command(name='create-project')
@click.argument('notificationscheme')
@click.argument('description')
@click.argument('lead')
@click.argument('url')
@click.argument('projecttemplatekey')
@click.argument('longname')
@click.argument('shortkey')
@click.argument('projecturl')
@click.pass_context
def create_project(ctx, notificationscheme, description, lead, url, projecttemplatekey, longname, shortkey, projecturl):
    """Create a JIRA project.

    \b
    notificationscheme: 10000 is the global default
    lead: lfid of the project lead. (lead must have previously signed in to jira)
    url: jira.example.com
    projectTemplateKey: Valid values are one of the following
    com.pyxis.greenhopper.jira:gh-scrum-template
    com.pyxis.greenhopper.jira:gh-kanban-template
    com.pyxis.greenhopper.jira:basic-software-development-template
    longname: Long project name, please double quote.
    shortkey: Ten character SHORTKEY must be capitalized
    projecturl: Projects URL, probaly a link to their wiki.

    TODO: do we need to add these as options?
    issueSecurityScheme: 10001,
    categoryId: 10120

    Example:
    lftools jira create-project 10000 "example description" adminlfid jira.example.com com.pyxis.greenhopper.jira:gh-scrum-template "Example test project" EXAMPLE https://wiki.example.com/exampleproject
    """
    userandpass = config.get_setting("jira", "base64")
    url = ("https://{}/rest/api/2/project/").format(url)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Basic %s" % userandpass
    }

    payload = json.dumps({
        "notificationScheme": "{}".format(notificationscheme),  # 10000 make a default
        "description": "{}".format(description),
        "lead": "{}".format(lead),
        "url": "{}".format(projecturl),
        "projectTemplateKey": "{}".format(projecttemplatekey),
        "name": "{}".format(longname),  # 80 chars
        "permissionScheme": 0,  # this is default
        "assigneeType": "PROJECT_LEAD",
        "projectTypeKey": "software",
        "key": "{}".format(shortkey),  # 10 chars
    })

    log.info(payload)
    response = requests.request(
        "POST",
        url,
        data=payload,
        headers=headers
    )
    if response.status_code in (200, 201):
        try:
            resp_json = response.json()
            log.info(json.dumps(resp_json, sort_keys=True, indent=4,
                                separators=(",", ": ")))
        except ValueError:
            log.info("Success response is not valid JSON. Raw response text:")
            log.info(response.text)
    else:
        log.error("Jira project creation failed with status code "
                  + str(response.status_code))


@click.command(name='set-owner')
@click.argument('jiraurl')
@click.argument('currentgroup')
@click.argument('projectkey')
@click.argument('role')
@click.pass_context
def set_owner(ctx, jiraurl, currentgroup, projectkey, role):
    """Set an ldap group as owner on a jira project. 1002 is the role for owner, 1001 is devloper.

    \b
    Example: jira.example.com ldap-group-committers PROJECTSHORTKEY 1002
    Rolls may be diffrent across jiras.
    find admin role with lftools jira get-scheme jira.example.com role
    """
    userandpass = config.get_setting("jira", "base64")
    url = ("https://{}/rest/api/2/project/{}/role/{}").format(jiraurl, projectkey, role)

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Basic %s" % userandpass
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

    log.info(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))


jira.add_command(get_scheme)
jira.add_command(create_project)
jira.add_command(set_owner)
