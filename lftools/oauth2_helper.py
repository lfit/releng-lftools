# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Helper script to get access_token for lfid api."""

import json

import httplib2
from oauth2client import client

from lftools import config


def oauth_helper():
    """Helper script to get access_token for lfid api."""
    client_id = config.get_setting("lfid", "ClientID")
    client_secret = config.get_setting("lfid", "CLIENT_SECRET")
    refresh_token = config.get_setting("lfid", "REFRESH_TOKEN")
    token_uri = config.get_setting("lfid", "TOKEN_URI")
    url = config.get_setting("lfid", "URL")

    credentials = client.OAuth2Credentials(
        access_token=None,  # set access_token to None since we use a refresh token
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
        token_expiry=None,
        token_uri=token_uri,
        user_agent=None)
    credentials.refresh(httplib2.Http())
    key = json.loads(credentials.to_json())
    access_token = (key['access_token'])
    return access_token, url
