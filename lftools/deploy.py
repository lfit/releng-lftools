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

import logging
import os
import re
import shutil
import sys
import zipfile

import glob2  # Switch to glob when Python < 3.5 support is dropped
import requests

log = logging.getLogger(__name__)


def _log_error_and_exit(msg1=None, msg2=None):
    """Print error message, and exit."""
    if msg1:
        log.error(msg1)
    if msg2:
        log.error(msg2)
    sys.exit(1)


def _format_url(url):
    """Ensure url starts with http and trim trailing '/'s."""
    start_pattern = re.compile('^(http|https)://')
    if not start_pattern.match(url):
        url = 'http://{}'.format(url)

    if url.endswith('/'):
        url = url.rstrip('/')

    return url


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

    try:
        _upload_file = open(zip_file, 'rb')
    except IOError:
        _log_error_and_exit("ZIP file not found: {}".format(zip_file))
    except FileNotFoundError:
        _log_error_and_exit("ZIP file not found: {}".format(zip_file))
    except PermissionError:
        _log_error_and_exit("Can not read ZIP file, wrong permissions: {}".format(zip_file))
    files = {'file': _upload_file}
    try:
        resp = requests.post(url, files=files)
    except Exception as e:
        _log_error_and_exit("Not valid nexus URL: {}".format(nexus_url), e)
    finally:
        _upload_file.close()
    log.debug('{}: {}'.format(resp.status_code, resp.text))

    if resp.status_code == 404:
        _log_error_and_exit("Did not find repository with id: {}".format(nexus_repo))
    if resp.status_code == 400:
        _log_error_and_exit("Repository is read only: {}".format(nexus_repo))

    if not str(resp.status_code).startswith('20'):
        _log_error_and_exit("Failed to upload with: {}:{}".format(
            resp.status_code, resp.text), zipfile.ZipFile(zip_file).infolist())
