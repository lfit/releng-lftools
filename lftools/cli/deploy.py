# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Script to deploy files to a Nexus sites repository."""

__author__ = "Thanh Ha"


import logging
import subprocess
import sys

import click
from requests.exceptions import HTTPError

import lftools.deploy as deploy_sys

log = logging.getLogger(__name__)


@click.group()
@click.pass_context
def deploy(ctx):
    """Deploy files to a Nexus sites repository.

    Deploy commands use ~/.netrc for authentication. This file should be
    pre-configured with an entry for the Nexus server. Eg.

        \b
        machine nexus.opendaylight.org login logs_user password logs_password
    """
    pass


@click.command()
@click.argument("nexus-url", envvar="NEXUS_URL")
@click.argument("nexus-path", envvar="NEXUS_PATH")
@click.argument("workspace", envvar="WORKSPACE")
@click.option("-p", "--pattern", multiple=True)
@click.pass_context
def archives(ctx, nexus_url, nexus_path, workspace, pattern):
    """Archive files to a Nexus site repository.

    Provides 2 ways to archive files:

        \b
        1) globstar pattern provided by the user.
        2) $WORKSPACE/archives directory provided by the user.

    To use this command the Nexus server must have a site repository configured
    with the name "logs" as this is a hardcoded log path.
    """
    if not pattern:
        pattern = None

    try:
        deploy_sys.deploy_archives(nexus_url, nexus_path, workspace, pattern)
    except HTTPError as e:
        log.error(str(e))
        sys.exit(1)
    except OSError as e:
        deploy_sys._log_error_and_exit(str(e))

    log.info("Archives upload complete.")


@click.command(name="copy-archives")
@click.argument("workspace", envvar="WORKSPACE")
@click.argument("pattern", nargs=-1, default=None, required=False)
@click.pass_context
def copy_archives(ctx, workspace, pattern):
    """Copy files for archiving.

    Arguments:

        workspace: Typically a Jenkins WORKSPACE to copy files from.
        pattern: Space-separated list of Unix style glob patterns of files to
            copy for archiving. (default: false)
    """
    deploy_sys.copy_archives(workspace, pattern)


@click.command()
@click.argument("nexus-url", envvar="NEXUS_URL")
@click.argument("nexus-repo-id")
@click.argument("group-id")
@click.argument("artifact-id")
@click.argument("version")
@click.argument("packaging")
@click.argument("file")
@click.option("-c", "--classifier", default="")
@click.pass_context
def file(ctx, nexus_url, nexus_repo_id, group_id, artifact_id, version, packaging, classifier, file):
    """Upload file to Nexus as a Maven artifact using cURL.

    This function will upload an artifact to Nexus while providing all of
    the usual Maven pom.xml information so that it conforms to Maven 2 repo
    specs.
    """
    try:
        deploy_sys.upload_maven_file_to_nexus(
            nexus_url, nexus_repo_id, group_id, artifact_id, version, packaging, file, classifier
        )
    except HTTPError as e:
        log.error(str(e))
        sys.exit(1)

    log.info("Upload maven file to nexus completed.")


@click.command()
@click.argument("nexus-url", envvar="NEXUS_URL")
@click.argument("nexus-path", envvar="NEXUS_PATH")
@click.argument("build-url", envvar="BUILD_URL")
@click.pass_context
def logs(ctx, nexus_url, nexus_path, build_url):
    """Deploy logs to a Nexus site repository.

    This script fetches logs and system information and pushes them to Nexus
    for log archiving.

    To use this script the Nexus server must have a site repository configured
    with the name "logs" as this is a hardcoded path.
    """
    try:
        deploy_sys.deploy_logs(nexus_url, nexus_path, build_url)
    except HTTPError as e:
        log.error(str(e))
        sys.exit(1)

    log.info("Logs upload complete.")


@click.command(name="s3")
@click.argument("s3_bucket", envvar="S3_BUCKET")
@click.argument("s3_path")
@click.argument("build-url", envvar="BUILD_URL")
@click.argument("workspace", envvar="WORKSPACE")
@click.option("-p", "--pattern", multiple=True)
@click.pass_context
def s3(ctx, s3_bucket, s3_path, build_url, workspace, pattern):
    """Deploy logs and archives to a S3 bucket."""
    if not pattern:
        pattern = None
        deploy_sys.deploy_s3(s3_bucket, s3_path, build_url, workspace, pattern)
    log.info("Logs upload to S3 complete.")


@click.command(name="maven-file")
@click.argument("nexus-url", envvar="NEXUS_URL")
@click.argument("repo-id", envvar="REPO_ID")
@click.argument("file-name", envvar="FILE_NAME")

# Maven Config
@click.option("-b", "--maven-bin", envvar="MAVEN_BIN", help="Path of maven binary.")
@click.option("-gs", "--global-settings", envvar="GLOBAL_SETTINGS_FILE", help="Global settings file.")
@click.option("-s", "--settings", envvar="SETTINGS_FILE", help="Settings file.")
@click.option("-p", "--maven-params", help="Pass Maven commandline options to the mvn command.")
# Maven Artifact GAV
@click.option("-a", "--artifact-id", help="Maven Artifact ID.")
@click.option("-c", "--classifier", help="File classifier.")
@click.option("-f", "--pom-file", help="Pom file to extract GAV information from.")
@click.option("-g", "--group-id", help="Maven Group ID")
@click.option("-v", "--version", help="Maven artifact version.")
@click.pass_context
def maven_file(
    # Maven Config
    ctx,
    nexus_url,
    repo_id,
    file_name,
    maven_bin,
    global_settings,
    settings,
    maven_params,
    # Maven GAV
    artifact_id,
    group_id,
    classifier,
    version,
    pom_file,
):
    """Deploy a file to a Nexus maven2 repository.

    As this script uses mvn to deploy. The server configuration should be
    configured in your local settings.xml. By default the script uses the
    mvn default "~/.m2/settings.xml" for the configuration but this can be
    overrided in the following order:

        \b
        1. Passed through CLI option "-s" ("-gs" for global-settings)
        2. Environment variable "$SETTINGS_FILE" ("$GLOBAL_SETTINGS_FILE" for global-settings)
        3. Maven default "~/.m2/settings.xml".

    If pom-file is passed in via the "-f" option then the Maven GAV parameters
    are not necessary. pom-file setting overrides the Maven GAV parameters.
    """
    params = ["deploy", "maven-file"]

    # Maven Configuration
    if maven_bin:
        params.extend(["-b", maven_bin])
    if global_settings:
        params.extend(["-l", global_settings])
    if settings:
        params.extend(["-s", settings])
    if maven_params:
        params.extend(["-p", maven_params])

    # Maven Artifact GAV
    if artifact_id:
        params.extend(["-a", artifact_id])
    if classifier:
        params.extend(["-c", classifier])
    if group_id:
        params.extend(["-g", group_id])
    if pom_file:
        params.extend(["-f", pom_file])
    if version:
        params.extend(["-v", version])

    # Set required variables last as getopts get's processed first.
    params.extend([nexus_url, repo_id, file_name])

    status = subprocess.call(params)
    sys.exit(status)


@click.command()
@click.argument("nexus-repo-url", envvar="NEXUS_REPO_URL")
@click.argument("deploy-dir", envvar="DEPLOY_DIR")
@click.option("-s", "--snapshot", is_flag=True, default=False, help="Deploy a snapshot repo.")
@click.pass_context
def nexus(ctx, nexus_repo_url, deploy_dir, snapshot):
    """Deploy a Maven repository to a specified Nexus repository.

    This script takes a local Maven repository and deploys it to a Nexus
    repository.

    Example Repository:

        https://nexus.example.org/content/repositories/release
    """
    log.debug("nexus_repo_url={}, deploy_dir={}, snapshot={}".format(nexus_repo_url, deploy_dir, snapshot))
    try:
        deploy_sys.deploy_nexus(nexus_repo_url, deploy_dir, snapshot)
    except IOError as e:
        deploy_sys._log_error_and_exit(str(e))
    except HTTPError as e:
        deploy_sys._log_error_and_exit(str(e))


@click.command(name="nexus-stage")
@click.argument("nexus-url", envvar="NEXUS_URL")
@click.argument("staging-profile-id", envvar="STAGING_PROFILE_ID")
@click.argument("deploy-dir", envvar="DEPLOY_DIR")
@click.pass_context
def nexus_stage(ctx, nexus_url, staging_profile_id, deploy_dir):
    """Deploy a Maven repository to a Nexus staging repository.

    This script takes a local Maven repository and deploys it to a Nexus
    staging repository as defined by the staging-profile-id.
    """
    deploy_sys.deploy_nexus_stage(nexus_url, staging_profile_id, deploy_dir)


@click.command(name="nexus-stage-repo-close")
@click.argument("nexus-url", envvar="NEXUS_URL")
@click.argument("staging-profile-id", envvar="STAGING_PROFILE_ID")
@click.argument("staging-repo-id")
@click.pass_context
def nexus_stage_repo_close(ctx, nexus_url, staging_profile_id, staging_repo_id):
    """Close a Nexus staging repo."""
    deploy_sys.nexus_stage_repo_close(nexus_url, staging_profile_id, staging_repo_id)


@click.command(name="nexus-stage-repo-create")
@click.argument("nexus-url", envvar="NEXUS_URL")
@click.argument("staging-profile-id", envvar="STAGING_PROFILE_ID")
@click.pass_context
def nexus_stage_repo_create(ctx, nexus_url, staging_profile_id):
    """Create a Nexus staging repo."""
    staging_repo_id = deploy_sys.nexus_stage_repo_create(nexus_url, staging_profile_id)
    log.info(staging_repo_id)


@click.command(name="nexus-zip")
@click.argument("nexus-url", envvar="NEXUS_URL")
@click.argument("nexus-repo", envvar="NEXUS_REPO")
@click.argument("nexus-path", envvar="NEXUS_PATH")
@click.argument("deploy-zip", envvar="DEPLOY_DIR")
@click.pass_context
def nexus_zip(ctx, nexus_url, nexus_repo, nexus_path, deploy_zip):
    """Deploy zip file containing artifacts to Nexus using cURL.

    This script simply takes a zip file preformatted in the correct
    directory for Nexus and uploads to a specified Nexus repo using the
    content-compressed URL.

    Requires the Nexus Unpack plugin and permission assigned to the upload user.
    """
    try:
        deploy_sys.deploy_nexus_zip(nexus_url, nexus_repo, nexus_path, deploy_zip)
    except IOError as e:
        log.error(str(e))
        sys.exit(1)
    except HTTPError as e:
        log.error(str(e))
        sys.exit(1)

    log.info("Zip file upload complete.")


deploy.add_command(archives)
deploy.add_command(copy_archives)
deploy.add_command(file)
deploy.add_command(logs)
deploy.add_command(maven_file)
deploy.add_command(nexus)
deploy.add_command(nexus_stage)
deploy.add_command(nexus_stage_repo_close)
deploy.add_command(nexus_stage_repo_create)
deploy.add_command(nexus_zip)
deploy.add_command(s3)
