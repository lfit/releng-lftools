# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Verify YAML Schema."""

"""Script to insert missing values from ldap into a projects INFO.yaml."""

import json
import logging
import click
import httplib2
from oauth2client import client
import requests

from xdg import XDG_CONFIG_HOME
from lftools import config


def oauth_helper():
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
    access_token = (KEY['access_token'])
    return access_token

#oauth_helper()
