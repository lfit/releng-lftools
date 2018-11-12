# -*- coding: utf-8 -*-
# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Library of functions for deploying artifacts to Nexus."""

import gzip
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

from defusedxml.minidom import parseString
import glob2  # Switch to glob when Python < 3.5 support is dropped
import requests

log = logging.getLogger(__name__)


def _compress_text(dir):
    """Compress all text files in directory."""
    save_dir = os.getcwd()
    os.chdir(dir)

    compress_types = [
        '**/*.log',
        '**/*.txt',
    ]
    paths = []
    for _type in compress_types:
        search = os.path.join(dir, _type)
        paths.extend(glob2.glob(search, recursive=True))

    for _file in paths:
        with open(_file, 'rb') as src, gzip.open('{}.gz'.format(_file), 'wb') as dest:
            shutil.copyfileobj(src, dest)
            os.remove(_file)

    os.chdir(save_dir)


def _format_url(url):
    """Ensure url starts with http and trim trailing '/'s."""
    start_pattern = re.compile('^(http|https)://')
    if not start_pattern.match(url):
        url = 'http://{}'.format(url)

    if url.endswith('/'):
        url = url.rstrip('/')

    return url


def _log_error_and_exit(*msg_list):
    """Print error message, and exit."""
    for msg in msg_list:
        log.error(msg)
    sys.exit(1)


def _request_post(url, data, headers):
    """Execute a request post, return the resp."""
    resp = {}
    try:
        resp = requests.post(url, data=data, headers=headers)
    except requests.exceptions.MissingSchema:
        log.debug("in _request_post. MissingSchema")
        _log_error_and_exit("Not valid URL: {}".format(url))
    except requests.exceptions.ConnectionError:
        log.debug("in _request_post. ConnectionError")
        _log_error_and_exit("Could not connect to URL: {}".format(url))
    except requests.exceptions.InvalidURL:
        log.debug("in _request_post. InvalidURL")
        _log_error_and_exit("Invalid URL: {}".format(url))
    return resp


def _get_node_from_xml(xml_data, tag_name):
    """Extract tag data from xml data."""
    log.debug('xml={}'.format(xml_data))

    try:
        dom1 = parseString(xml_data)
        childnode = dom1.getElementsByTagName(tag_name)[0]
    except:
        _log_error_and_exit("Received bad XML, can not find tag {}".format(tag_name), xml_data)
    return childnode.firstChild.data


def copy_archives(workspace, pattern=None):
    """Copy files matching PATTERN in a WORKSPACE to the current directory.

    The best way to use this function is to cd into the directory you wish to
    store the files first before calling the function.

    This function provides 2 ways to archive files:

        1) copy $WORKSPACE/archives directory
        2) copy globstar pattern

    :params:

        :arg str pattern: Space-separated list of Unix style glob patterns.
            (default: None)
    """
    archives_dir = os.path.join(workspace, 'archives')
    dest_dir = os.getcwd()

    log.debug('Copying files from {} with pattern \'{}\' to {}.'.format(
        workspace, pattern, dest_dir))
    for file_or_dir in os.listdir(archives_dir):
        f = os.path.join(archives_dir, file_or_dir)
        try:
            log.debug('Moving {}'.format(f))
            shutil.move(f, dest_dir)
        except shutil.Error as e:
            log.warn(e)

    if pattern is None:
        return

    paths = []
    for p in pattern:
        search = os.path.join(workspace, p)
        paths.extend(glob2.glob(search, recursive=True))
    log.debug('Files found: {}'.format(paths))

    for src in paths:
        if len(os.path.basename(src)) > 255:
            log.warn('Filename {} is over 255 characters. Skipping...'.format(
                os.path.basename(src)))

        dest = os.path.join(dest_dir, src[len(workspace)+1:])
        log.debug('{} -> {}'.format(src, dest))

        try:
            shutil.move(src, dest)
        except IOError as e:  # Switch to FileNotFoundError when Python 2 support is dropped.
            log.debug(e)
            os.makedirs(os.path.dirname(dest))
            shutil.move(src, dest)


def deploy_archives(nexus_url, nexus_path, workspace, pattern=None):
    """Archive files to a Nexus site repository named logs.

    Provides 2 ways to archive files:
        1) $WORKSPACE/archives directory provided by the user.
        2) globstar pattern provided by the user.

    Requirements:

    To use this API a Nexus server must have a site repository configured
    with the name "logs" as this is a hardcoded path.

    Parameters:

        :nexus_url: URL of Nexus server. Eg: https://nexus.opendaylight.org
        :nexus_path: Path on nexus logs repo to place the logs. Eg:
            $SILO/$JENKINS_HOSTNAME/$JOB_NAME/$BUILD_NUMBER
        :workspace: Directory in which to search, typically in Jenkins this is
            $WORKSPACE
        :pattern: Space-separated list of Globstar patterns of files to
            archive. (optional)
    """
    nexus_url = _format_url(nexus_url)
    work_dir = tempfile.mkdtemp(prefix='lftools-da.')
    os.chdir(work_dir)
    log.debug('workspace: {}, work_dir: {}'.format(workspace, work_dir))

    copy_archives(workspace, pattern)
    _compress_text(work_dir)

    archives_zip = shutil.make_archive(
        '{}/archives'.format(workspace), 'zip')
    log.debug('archives zip: {}'.format(archives_zip))
    deploy_nexus_zip(nexus_url, 'logs', nexus_path, archives_zip)
    shutil.rmtree(work_dir)


def deploy_logs(nexus_url, nexus_path, build_url):
    """Deploy logs to a Nexus site repository named logs.

    Fetches logs and system information and pushes them to Nexus
    for log archiving.
    Requirements:

    To use this API a Nexus server must have a site repository configured
    with the name "logs" as this is a hardcoded path.

    Parameters:

        :nexus_url: URL of Nexus server. Eg: https://nexus.opendaylight.org
        :nexus_path: Path on nexus logs repo to place the logs. Eg:
            $SILO/$JENKINS_HOSTNAME/$JOB_NAME/$BUILD_NUMBER
        :build_url: URL of the Jenkins build. Jenkins typically provides this
                    via the $BUILD_URL environment variable.
    """
    nexus_url = _format_url(nexus_url)
    work_dir = tempfile.mkdtemp(prefix='lftools-dl.')
    os.chdir(work_dir)
    log.debug('work_dir: {}'.format(work_dir))

    build_details = open('_build-details.log', 'w+')
    build_details.write('build-url: {}'.format(build_url))

    with open('_sys-info.log', 'w+') as sysinfo_log:
        sys_cmds = []

        log.debug('Platform: {}'.format(sys.platform))
        if sys.platform == "linux" or sys.platform == "linux2":
            sys_cmds = [
                ['uname', '-a'],
                ['lscpu'],
                ['nproc'],
                ['df', '-h'],
                ['free', '-m'],
                ['ip', 'addr'],
                ['sar', '-b', '-r', '-n', 'DEV'],
                ['sar', '-P', 'ALL'],
            ]

        for c in sys_cmds:
            try:
                output = subprocess.check_output(c).decode('utf-8')
            except OSError:  # TODO: Switch to FileNotFoundError when Python < 3.5 support is dropped.
                log.debug('Command not found: {}'.format(c))
                continue

            output = '---> {}:\n{}\n'.format(' '.join(c), output)
            sysinfo_log.write(output)
            log.info(output)

    build_details.close()

    # Magic string used to trim console logs at the appropriate level during wget
    MAGIC_STRING = "-----END_OF_BUILD-----"
    log.info(MAGIC_STRING)

    resp = requests.get('{}/consoleText'.format(_format_url(build_url)))
    with open('console.log', 'w+') as f:
        f.write(resp.text.split(MAGIC_STRING)[0])

    resp = requests.get('{}/timestamps?time=HH:mm:ss&appendLog'.format(_format_url(build_url)))
    with open('console-timestamp.log', 'w+') as f:
        f.write(resp.text.split(MAGIC_STRING)[0])

    _compress_text(work_dir)

    console_zip = tempfile.NamedTemporaryFile(prefix='lftools-dl', delete=True)
    log.debug('console-zip: {}'.format(console_zip.name))
    shutil.make_archive(console_zip.name, 'zip', work_dir)
    deploy_nexus_zip(nexus_url, 'logs', nexus_path, '{}.zip'.format(console_zip.name))
    console_zip.close()
    shutil.rmtree(work_dir)


def deploy_nexus_zip(nexus_url, nexus_repo, nexus_path, zip_file):
    """"Deploy zip file containing artifacts to Nexus using requests.

    This function simply takes a zip file preformatted in the correct
    directory for Nexus and uploads to a specified Nexus repo using the
    content-compressed URL.

    Requires the Nexus Unpack plugin and permission assigned to the upload user.

    Parameters:

        nexus_url:    URL to Nexus server. (Ex: https://nexus.opendaylight.org)
        nexus_repo:   The repository to push to. (Ex: site)
        nexus_path:   The path to upload the artifacts to. Typically the
                      project group_id depending on if a Maven or Site repo
                      is being pushed.
                      Maven Ex: org/opendaylight/odlparent
                      Site Ex: org.opendaylight.odlparent
        zip_file:     The zip to deploy. (Ex: /tmp/artifacts.zip)
    """
    url = '{}/service/local/repositories/{}/content-compressed/{}'.format(
        _format_url(nexus_url),
        nexus_repo,
        nexus_path)
    log.debug('Uploading {} to {}'.format(zip_file, url))

    upload_file = open(zip_file, 'rb')

    files = {'file': upload_file}
    resp = requests.post(url, files=files)
    log.debug('{}: {}'.format(resp.status_code, resp.text))

    if resp.status_code == 400:
        raise requests.HTTPError("Repository is read only: {}".format(nexus_repo))
    elif resp.status_code == 404:
        raise requests.HTTPError("Did not find repository with ID: {}".format(nexus_repo))

    if not str(resp.status_code).startswith('20'):
        raise requests.HTTPError("Failed to upload to Nexus with status code: {}.\n{}\n{}".format(
            resp.status_code, resp.text, zipfile.ZipFile(zip_file).infolist()))


def nexus_stage_repo_create(nexus_url, staging_profile_id):
    """Create a Nexus staging repo.

    Parameters:
    nexus_url:           URL to Nexus server. (Ex: https://nexus.example.org)
    staging_profile_id:  The staging profile id as defined in Nexus for the
                         staging repo.

    Returns:             staging_repo_id

    Sample:
    lftools deploy nexus-stage-repo-create 192.168.1.26:8081/nexsus/ 93fb68073c18
    """
    nexus_url = '{0}/service/local/staging/profiles/{1}/start'.format(
        _format_url(nexus_url),
        staging_profile_id)

    log.debug("Nexus URL           = {}".format(nexus_url))

    xml = """
        <promoteRequest>
            <data>
                <description>Create staging repository.</description>
            </data>
        </promoteRequest>
    """

    headers = {'Content-Type': 'application/xml'}
    resp = _request_post(nexus_url, xml, headers)

    log.debug("resp.status_code = {}".format(resp.status_code))
    log.debug("resp.text = {}".format(resp.text))

    if re.search('nexus-error', resp.text):
        error_msg = _get_node_from_xml(resp.text, 'msg')
        if re.search('.*profile with id:.*does not exist.', error_msg):
            _log_error_and_exit("Staging profile id {} not found.".format(staging_profile_id))
        _log_error_and_exit(error_msg)

    if resp.status_code == 405:
        _log_error_and_exit("HTTP method POST is not supported by this URL", nexus_url)
    if resp.status_code == 404:
        _log_error_and_exit("Did not find nexus site: {}".format(nexus_url))
    if not resp.status_code == 201:
        _log_error_and_exit("Failed with status code {}".format(resp.status_code), resp.text)

    staging_repo_id = _get_node_from_xml(resp.text, 'stagedRepositoryId')
    log.debug("staging_repo_id = {}".format(staging_repo_id))

    return staging_repo_id


def nexus_stage_repo_close(nexus_url, staging_profile_id, staging_repo_id):
    """Close a Nexus staging repo.

    Parameters:
    nexus_url:          URL to Nexus server. (Ex: https://nexus.example.org)
    staging_profile_id: The staging profile id as defined in Nexus for the
                        staging repo.
    staging_repo_id:    The ID of the repo to close.

    Sample:
    lftools deploy nexus-stage-repo-close 192.168.1.26:8081/nexsus/ 93fb68073c18 test1-1031
    """
    nexus_url = '{0}/service/local/staging/profiles/{1}/finish'.format(
        _format_url(nexus_url),
        staging_profile_id)

    log.debug("Nexus URL           = {}".format(nexus_url))
    log.debug("staging_repo_id     = {}".format(staging_repo_id))

    xml = """
        <promoteRequest>
            <data>
                <stagedRepositoryId>{0}</stagedRepositoryId>
                <description>Close staging repository.</description>
            </data>
        </promoteRequest>
    """.format(staging_repo_id)

    headers = {'Content-Type': 'application/xml'}
    resp = _request_post(nexus_url, xml, headers)

    log.debug("resp.status_code = {}".format(resp.status_code))
    log.debug("resp.text = {}".format(resp.text))

    if re.search('nexus-error', resp.text):
        error_msg = _get_node_from_xml(resp.text, 'msg')
    else:
        error_msg = resp.text

    if resp.status_code == 404:
        _log_error_and_exit("Did not find nexus site: {}".format(nexus_url))

    if re.search('invalid state: closed', error_msg):
        _log_error_and_exit("Staging repository is already closed.")
    if re.search('Missing staging repository:', error_msg):
        _log_error_and_exit("Staging repository do not exist.")

    if not resp.status_code == 201:
        _log_error_and_exit("Failed with status code {}".format(resp.status_code), resp.text)
