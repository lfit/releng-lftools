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
import shutil
import sys

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


def _request_post(in_url, in_data, in_headers):
    """Execute a request post, return the resp."""
    resp = {}
    try:
        resp = requests.post(in_url, data=in_data, headers=in_headers)
    except requests.exceptions.MissingSchema:
        _log_error_and_exit("Not valid URL: {}".format(in_url))
    except requests.exceptions.ConnectionError:
        _log_error_and_exit("Could not connect to URL: {}".format(in_url))
    except requests.exceptions.InvalidURL:
        _log_error_and_exit("Invalid URL: {}".format(in_url))
    return resp


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
