# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2018, 2023 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Jenkins token functions."""
from __future__ import annotations

__author__ = "Thanh Ha"

import logging

import jenkins

log: logging.Logger = logging.getLogger(__name__)


def get_token(name: str, url: str, username: str, password: str, change: bool = False) -> str:
    """Get API token.

    This function uses the global username / password for Jenkins from
    lftools.ini as the user asking for the token may not already know the
    api token.
    """
    if change:
        log.debug("Resetting Jenkins API token on {}".format(url))
    else:
        log.debug("Fetching Jenkins API token from {}".format(url))

    server: jenkins.Jenkins = jenkins.Jenkins(url, username=username, password=password)  # type: ignore

    get_token: str = (
        """
import hudson.model.*
import jenkins.model.*
import jenkins.security.*
import jenkins.security.apitoken.*
User u = User.get("{}")
ApiTokenProperty t = u.getProperty(ApiTokenProperty.class)
def token = t.tokenStore.generateNewToken("{}")
println token.plainValue
""".format(
            username, name
        )
    )

    token: str = str(server.run_script(get_token))
    return token
