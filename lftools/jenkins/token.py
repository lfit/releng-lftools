# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2018 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Jenkins token functions."""

__author__ = 'Thanh Ha'

import logging

import jenkins

from lftools import config

log = logging.getLogger(__name__)


def get_token(url, change=False):
    """Get API token.

    This function uses the global username / password for Jenkins from
    lftools.ini as the user asking for the token may not already know the
    api token.
    """
    change_token = '//'
    username = config.get_setting('global', 'username')
    password = config.get_setting('global', 'password')
    log.debug('Jenkins {} {}:{}'.format(url, username, password))

    server = jenkins.Jenkins(
        url,
        username=username,
        password=password)

    if change:
        change_token = ''

    get_token = """
import jenkins.security.*
User u = User.get("{}")
ApiTokenProperty t = u.getProperty(ApiTokenProperty.class)
{}t.changeApiToken()
def token = t.getApiToken()
println "$token"
""".format(username, change_token)

    token = server.run_script(get_token)
    return token
