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
        _log_error_and_exit("Not valid URL: {}".format(url))
    except requests.exceptions.ConnectionError:
        _log_error_and_exit("Could not connect to URL: {}".format(url))
    except requests.exceptions.InvalidURL:
        _log_error_and_exit("Invalid URL: {}".format(url))
    return resp


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

    # TODO: Update to use I58ea1d7703b626f791dcd74e63251c4f3261ca7d once it's available.
    upload_files = {'upload_file': open(archives_zip, 'rb')}
    url = '{}/service/local/repositories/logs/content-compressed/{}'.format(
        nexus_url, nexus_path)
    r = requests.post(url, files=upload_files)
    log.debug('{}: {}'.format(r.status_code, r.text))
    if r.status_code != 201:
        log.error('Failed to upload to Nexus with status code {}.\n{}'.format(
            r.status_code, r.content))
        sys.exit(1)

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
    log.debug('listdir: {}'.format(os.listdir(work_dir)))

    # TODO: Update to use I58ea1d7703b626f791dcd74e63251c4f3261ca7d once it's available.
    upload_files = {'upload_file': open('{}.zip'.format(console_zip.name), 'rb')}
    url = '{}/service/local/repositories/logs/content-compressed/{}'.format(
        nexus_url, nexus_path)
    r = requests.post(url, files=upload_files)
    log.debug('{}: {}'.format(r.status_code, r.text))
    if r.status_code != 201:
        log.error('Failed to upload to Nexus with status code {}.\n{}'.format(
            r.status_code, r.content))
        sys.exit(1)

    console_zip.close()
    shutil.rmtree(work_dir)
