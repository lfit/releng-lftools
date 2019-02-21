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
import logging
import click
import httplib2
from oauth2client import client
import requests

from xdg import XDG_CONFIG_HOME
from lftools import config

#LFTOOLS_CONFIG_FILE = '/'.join([XDG_CONFIG_HOME, 'lftools', 'lftools.ini'])

CLIENT_ID = config.get_setting("lfid", "ClientID")
CLIENT_SECRET = config.get_setting("lfid", "CLIENT_SECRET")
REFRESH_TOKEN = config.get_setting("lfid", "REFRESH_TOKEN")
TOKEN_URI = config.get_setting("lfid", "TOKEN_URI")

CREDENTIALS = client.OAuth2Credentials(
    access_token=None,  # set access_token to None since we use a refresh token
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    refresh_token=REFRESH_TOKEN,
    token_expiry=None,
    token_uri=TOKEN_URI,
    user_agent=None)
CREDENTIALS.refresh(httplib2.Http())
KEY = json.loads(CREDENTIALS.to_json())
ACCESS_TOKEN = (KEY['access_token'])

@click.group()
@click.pass_context
def lfidapi(ctx):
    """LFID API TOOLS."""
    pass


@click.command()
@click.argument('group')
@click.pass_context
def search_members(ctx, group):
    url = 'https://identitystg.linuxfoundation.org/rest/auth0/og/{}'.format(group)
    headers = {'Authorization': 'Bearer ' + ACCESS_TOKEN}
    response = requests.get(url, headers=headers)
    result = (response.json())
    print(response.status_code)
    #print(json.dumps(result, indent=4, sort_keys=True))

    members = result["members"]
    print(members)

    emails = []
    for member in members:
        emails.append(member["mail"])
        #email = member["mail"]
        #do-something-with-email-address(email)

    print(emails)

@click.command()
@click.argument('user')
@click.option('--delete', is_flag=True, required=False,
                         help='remove user from group')
@click.argument('group')
@click.pass_context
def user(ctx, user, group, delete):
    ##Dont need this
    #params = ['user']
    #if delete:
    #    params.extend([delete])
    #    print(params)
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
