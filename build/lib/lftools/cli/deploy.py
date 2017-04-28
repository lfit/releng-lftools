# @License EPL-1.0 <http://spdx.org/licenses/EPL-1.0>
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Script to deploy files to a Nexus sites repository."""

__author__ = 'Thanh Ha'


import subprocess

import click


@click.group()
@click.pass_context
def deploy(ctx):
    """Deploy files to a Nexus sites repository."""
    pass


@click.command()
@click.argument('nexus-url', envvar='NEXUS_URL')
@click.argument('nexus-path', envvar='NEXUS_PATH')
@click.argument('workspace', envvar='WORKSPACE')
@click.option('-p', '--pattern', default='')
@click.pass_context
def archives(ctx, nexus_url, nexus_path, workspace, pattern):
    """Archive files to a Nexus site repository.

    Provides 2 ways to archive files:

        \b
        1) globstar pattern provided by the user.
        2) $WORKSPACE/archives directory provided by the user.

    To use this script the Nexus server must have a site repository configured
    with the name "logs" as this is a hardcoded path. Also this script uses
    ~/.netrc for it's authentication which must be provided.
    """
    subprocess.call(['deploy', 'archives', nexus_url, nexus_path, workspace, pattern])


@click.command()
@click.argument('nexus-url', envvar='NEXUS_URL')
@click.argument('nexus-path', envvar='NEXUS_PATH')
@click.argument('build-url', envvar='BUILD_URL')
@click.pass_context
def logs(ctx, nexus_url, nexus_path, build_url):
    """Deploy logs to a Nexus site repository.

    This script fetches logs and system information and pushes them to Nexus
    for log archiving.

    To use this script the Nexus server must have a site repository configured
    with the name "logs" as this is a hardcoded path. Also this script uses
    ~/.netrc for it's authentication which must be provided.
    """
    subprocess.call(['deploy', 'logs', nexus_url, nexus_path, build_url])


deploy.add_command(archives)
deploy.add_command(logs)
