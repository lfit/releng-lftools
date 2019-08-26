# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Read the Docs api v3  tools."""

from __future__ import print_function

import json
import logging

import click
import requests

from lftools import config

log = logging.getLogger(__name__)


@click.group()
@click.pass_context
def rtd(ctx):
    """RTD v3 api tools."""
    pass


@click.command(name='get')
@click.argument('endpoint')
@click.pass_context
def get_scheme(ctx, endpoint):
    """Get request a jira end-point.
    """
    #$ curl -H "Authorization: Token <token>" https://readthedocs.org/api/v3/projects/
    url = ("https://readthedocs.org/api/v3/{}/lfit-sandbox-test").format(endpoint)
    # List all url = ("https://readthedocs.org/api/v3/{}").format(endpoint)
    token = config.get_setting("rtd", "token")
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Token %s" % token
    }

    response = requests.request(
        "GET",
        url,
        headers=headers
    )
    log.info(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))

#Triger a build 
# POST /api/v3/projects/(string: project_slug)/versions/(string: version_slug)/builds/
#$ curl \
#  -X POST \
#  -H "Authorization: Token <token>" https://readthedocs.org/api/v3/projects/lfit-sandbox-test/versions/latest/builds/


@click.command(name='create-project')
@click.argument('endpoint')
@click.argument('name')
@click.pass_context
def create_project(ctx, endpoint, name):
    """STUB"""

    url = ("https://readthedocs.org/api/v3/{}/").format(endpoint)
    token = config.get_setting("rtd", "token")

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Token %s" % token
    }

    payload = json.dumps({
        "name": "{}".format(name),  # 10000 make a default
        "repository": {
            "url": "https://github.com/lfit-sandbox/test",
            "type": "git"
        },
        "homepage": "http://lfit-sandbox-test.readthedocs.io/",
        "programming_language": "py",
        "language": "en"
    })

    log.info(payload)
    response = requests.request(
        "POST",
        url,
        data=payload,
        headers=headers
    )

    log.info(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))


rtd.add_command(get_scheme)
rtd.add_command(create_project)
