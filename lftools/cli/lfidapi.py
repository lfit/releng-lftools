#!/usr/bin/env python2
# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2018 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Script to insert missing values from ldap into a projects INFO.yaml."""

import json
import click
import requests
from lftools.oauth2_helper import oauth_helper

ACCESS_TOKEN = oauth_helper()

@click.group()
@click.pass_context
def lfidapi(ctx):
    """LFID API TOOLS."""
    pass

@click.command()
@click.argument('group')
@click.pass_context
def search_members(ctx, group):
    """ doc string """
    url = 'https://identitystg.linuxfoundation.org/rest/auth0/og/{}'.format(group)
    headers = {'Authorization': 'Bearer ' + ACCESS_TOKEN}
    response = requests.get(url, headers=headers)
    result = (response.json())
    print(response.status_code)

    members = result["members"]
    print(json.dumps(members, indent=4, sort_keys=True))

    #Just leaving this here incase we want to play with the output
    emails = []
    for member in members:
        emails.append(member["mail"])
    print(json.dumps(emails, indent=4, sort_keys=True))

@click.command()
@click.argument('user')
@click.option('--delete', is_flag=True, required=False,
                         help='remove user from group')
@click.argument('group')
@click.pass_context
def user(ctx, user, group, delete):
    """ doc string """
    url = 'https://identitystg.linuxfoundation.org/rest/auth0/og/{}'.format(group)
    headers = {'Authorization': 'Bearer ' + ACCESS_TOKEN}
    data = {"username": user }
    if delete:
        response = requests.delete(url, json=data, headers=headers)
    else:
        response = requests.put(url, json=data, headers=headers)
    result = (response.json())
    print(result)

@click.command()
@click.argument('email')
@click.argument('group')
@click.pass_context
def invite(ctx, email, group):
    """ doc string """
    url = 'https://identitystg.linuxfoundation.org/rest/auth0/og/{}/invite'.format(group)
    headers = {'Authorization': 'Bearer ' + ACCESS_TOKEN}
    data = {"mail": email }
    response = requests.put(url, json=data, headers=headers)
    result = (response.json())
    print(result)

@click.command()
@click.argument('group')
@click.pass_context
def create_group(ctx, group):
    """ doc string """
    url = 'https://identitystg.linuxfoundation.org/rest/auth0/og/'
    headers = {'Authorization': 'Bearer ' + ACCESS_TOKEN}
    data = {"title": group, "type": "group"}
    print(data)
    response = requests.post(url, json=data, headers=headers)
    result = (response.json())
    print(result)

lfidapi.add_command(search_members)
lfidapi.add_command(user)
lfidapi.add_command(invite)
lfidapi.add_command(create_group)
