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
import sys

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
    status = subprocess.call(['deploy', 'archives', nexus_url, nexus_path, workspace, pattern])
    sys.exit(status)


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
    status = subprocess.call(['deploy', 'logs', nexus_url, nexus_path, build_url])
    sys.exit(status)


@click.command(name='maven-file')
@click.argument('nexus-url', envvar='NEXUS_URL')
@click.argument('repo-id', envvar='REPO_ID')
@click.argument('group-id', envvar='GROUP_ID')
@click.argument('file-name', envvar='FILE_NAME')
@click.option('-c', '--classifier', envvar='CLASSIFIER', default='',
              help='File classifier.')
@click.option('-gs', '--global-settings-file', envvar='GLOBAL_SETTINGS_FILE',
              default='', help='Global settings file.')
@click.option('-s', '--settings-file', envvar='SETTINGS_FILE', default='',
              help='Settings file.')
@click.option('-m', '--maven-bin', envvar='MAVEN_BIN', default='',
              help='Path of maven binary.')
@click.pass_context
def maven_file(ctx, nexus_url, repo_id, group_id, file_name, classifier, global_settings_file, settings_file, maven_bin):
    """Deploy maven-file to a Nexus maven2 repository.

    To use this script the Nexus server must have a maven2 repository configured
    with capabilities. The script requires passing "~/.m2/settings.xml" file,
    passed either through command line options or through environment variables
    $GLOBAL_SETTINGS_FILE and $SETTINGS_FILE from the JJB configration.
    """
    status = subprocess.call(['deploy', 'maven-file', nexus_url, repo_id, group_id, file_name,
                              classifier, global_settings_file, settings_file, maven_bin])
    sys.exit(status)


@click.command()
@click.argument('nexus-repo-url', envvar='NEXUS_REPO_URL')
@click.argument('deploy-dir', envvar='DEPLOY_DIR')
@click.pass_context
def nexus(ctx, nexus_repo_url, deploy_dir):
    """Deploy a Maven repository to a specified Nexus repository.

    This script takes a local Maven repository and deploys it to a Nexus
    repository.

    Example Repository:

        https://nexus.example.org/content/repositories/release
    """
    status = subprocess.call(['deploy', 'nexus', nexus_repo_url, deploy_dir])
    sys.exit(status)


@click.command(name='nexus-stage')
@click.argument('nexus-url', envvar='NEXUS_URL')
@click.argument('staging-profile-id', envvar='STAGING_PROFILE_ID')
@click.argument('deploy-dir', envvar='DEPLOY_DIR')
@click.pass_context
def nexus_stage(ctx, nexus_url, staging_profile_id, deploy_dir):
    """Deploy a Maven repository to a Nexus staging repository.

    This script takes a local Maven repository and deploys it to a Nexus
    staging repository as defined by the staging-profile-id.
    """
    status = subprocess.call(['deploy', 'nexus-stage', nexus_url, staging_profile_id, deploy_dir])
    sys.exit(status)


deploy.add_command(archives)
deploy.add_command(maven_file)
deploy.add_command(logs)
deploy.add_command(nexus)
deploy.add_command(nexus_stage)
