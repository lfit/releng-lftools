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
import shutil
import sys
import tempfile

import glob2  # Switch to glob when Python < 3.5 support is dropped
import requests

log = logging.getLogger(__name__)


def copy_archives(workspace, pattern=None):
    """Copy files matching PATTERN in a WORKSPACE to the current directory.

    The best way to use this function is to cd into the directory you wish to
    store the files first before calling the function.

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

    Authentication is pulled in from ~/.config/lftools/lftools.ini

    Parameters:

        :nexus_url: URL of Nexus server. Eg: https://nexus.opendaylight.org
        :nexus_path: Path on nexus logs repo to place the logs. Eg:
            $SILO/$JENKINS_HOSTNAME/$JOB_NAME/$BUILD_NUMBER
        :workspace: Directory in which to search, typically in Jenkins this is
            $WORKSPACE
        :pattern: Space-separated list of Globstar patterns of files to
            archive. (optional)
    """
    work_dir = tempfile.mkdtemp(prefix='lftools-da.')
    os.chdir(work_dir)
    log.debug('workspace: {}, work_dir: {}'.format(workspace, work_dir))

    copy_archives(workspace, pattern)

    compress_types = [
        '**/*.log',
        '**/*.txt',
    ]
    paths = []
    for _type in compress_types:
        search = os.path.join(work_dir, _type)
        paths.extend(glob2.glob(search, recursive=True))

    for _file in paths:
        with open(_file, 'rb') as src, gzip.open('{}.gz'.format(_file), 'wb') as dest:
            shutil.copyfileobj(src, dest)
            os.remove(_file)

    archives_zip = shutil.make_archive(
        '{}/archives'.format(workspace), 'zip')
    log.debug('archives zip: {}'.format(archives_zip))

    upload_files = {'upload_file': open(archives_zip,'rb')}
    url = '{}/service/local/repositories/logs/content-compressed/{}'.format(
        nexus_url, nexus_path)
    r = requests.post(url, files=upload_files)
    log.debug('{}: {}'.format(r.status_code, r.text))

    if r.status_code != 201:
        log.error('Failed to upload to Nexus with status code {}. {}'.format(
            r.status_code, r.content))
        sys.exit(1)
    shutil.rmtree(work_dir)
