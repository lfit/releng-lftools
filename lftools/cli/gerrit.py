# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2018 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Create a gerrit project."""

from __future__ import print_function

import subprocess
import sys

import click


@click.group()
@click.pass_context
def gerrit_cli(ctx):
    """GERRIT TOOLS."""
    pass


@click.command(name='create')
@click.argument('gerrit_url')
@click.argument('ldap_group')
@click.argument('repo')
@click.argument('user')
@click.option('--enable', type=bool, required=False,
              help='Enable Repliaction to Github.')
@click.pass_context
def create(
        ctx, gerrit_url, ldap_group, repo, user, enable):
    """Create and configure permissions for a new gerrit repo.

    GERRIT_URL: gerrit.localhost

    LDAP_GROUP: project-gerrit-group-committers

    REPO: testrepo

    USER: user that has permissions in gerrit
    """
    params = ['gerrit_create']
    params.extend(["-p", gerrit_url])
    params.extend(["-d", ldap_group])
    params.extend(["-r", repo])
    params.extend(["-u", user])
    params.extend(["-e", enable])

    status = subprocess.call(params)
    sys.exit(status)


gerrit_cli.add_command(create)
