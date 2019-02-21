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
"""Use the LFIDAPI to add, remove and list members as well as create groups."""

import json
from urlparse import urljoin

import click
import requests
from validate_email import validate_email

from lftools.oauth2_helper import oauth_helper


@click.group()
@click.pass_context
def lfidapi(ctx):
    """LFID API TOOLS."""
    pass


@click.command()
@click.argument('group')
@click.pass_context
def search_members(ctx, group):
    """List members of a group."""
    access_token, url = oauth_helper()
    url = urljoin(url, group)
    headers = {'Authorization': 'Bearer ' + access_token}
    response = requests.get(url, headers=headers)
    result = (response.json())
    print(response.status_code)

    members = result["members"]
    print(json.dumps(members, indent=4, sort_keys=True))


@click.command()
@click.argument('user')
@click.option('--delete', is_flag=True, required=False,
              help='remove user from group')
@click.argument('group')
@click.pass_context
def user(ctx, user, group, delete):
    """Add and remove users from groups."""
    access_token, url = oauth_helper()
    url = urljoin(url, group)
    headers = {'Authorization': 'Bearer ' + access_token}
    data = {"username": user}
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
    """Email invitation to join group."""
    access_token, url = oauth_helper()
    # urljoin only accepts two variables
    prejoin = group + '/invite'
    url = urljoin(url, prejoin)
    headers = {'Authorization': 'Bearer ' + access_token}
    data = {"mail": email}
    print('Validating email', email)
    if validate_email(email):
        response = requests.post(url, json=data, headers=headers)
        result = (response.json())
        print(result)
    else:
        print("Email is not valid")


@click.command()
@click.argument('group')
@click.pass_context
def create_group(ctx, group):
    """Create group."""
    access_token, url = oauth_helper()
    url = '{}/'.format(url)
    headers = {'Authorization': 'Bearer ' + access_token}
    data = {"title": group, "type": "group"}
    print(data)
    response = requests.post(url, json=data, headers=headers)
    result = (response.json())
    print(result)


lfidapi.add_command(search_members)
lfidapi.add_command(user)
lfidapi.add_command(invite)
lfidapi.add_command(create_group)
