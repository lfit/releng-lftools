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
    print(json.dumps(result, indent=4, sort_keys=True))

    members = result["members"]
    emails = []
    for member in members:
        emails.append(member["mail"])
        #email = member["mail"]
        #do-something-with-email-address(email)
        print(emails)


@click.command()
@click.argument('user')
@click.argument('group')
@click.pass_context
def add_user(ctx, user, group):
    url = 'https://identitystg.linuxfoundation.org/rest/auth0/og/{}'.format(group)
    headers = {'Authorization': 'Bearer ' + ACCESS_TOKEN}
    #messing with context-type did not help
    #headers = {"Content-Type" : "application/json", "Authorization" : "Bearer " + ACCESS_TOKEN}
    #headers = {"Content-Type" : "application/json", 'Accept': 'text/plain', "authorization" : "Bearer " + ACCESS_TOKEN}
    
    #just put put it in hard coded for now.
    #data = {"username": user }
    data = {"username": "agardner" }
    print(data)

    #I think this should work... 

    response = requests.post(url, json=data, headers=headers)

#   I tried these..
#   Putting in the data = data did not work...
#   response = requests.post(url, data=data, headers=headers)
#   data=json.dumps(data) docs say this is no longer needed ...    
#   response = requests.post(url, data=json.dumps(data), headers=headers)
#   putting in the data directly didnt help.. as json= or data=
#   response = requests.post(url, json={"username": "agardner" }, headers=headers)
#   response = requests.post(url, data={"username": "agardner" }, headers=headers)

    result = (response.json())
    print(result)
    #getting ValueError: No JSON object could be decoded

lfidapi.add_command(search_members)
lfidapi.add_command(add_user)
