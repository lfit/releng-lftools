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

import glob2  # Switch to glob when Python < 3.5 support is dropped

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


def deploy_nexus_zip (nexus_url, nexus_repo, nexus_path, deploy_zip):
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
    deploy_zip:   The zip to deploy. (Ex: /tmp/artifacts.zip)
    """

    if len(nexus_url) == 0 or
        len(nexus_repo) == 0 or
        len(nexus_path) == 0 or
        len(deploy_zip) == 0:
        log.error("Not enough parameters")
        sys.exit(1)

    nexus_url = '{0}service/local/repositories/{1}/content-compressed/{2}'.format(
        local_format_url(nexus_url),
        nexus_repo,
        nexus_path)

    log.debug("nexus_url  = {}".format(nexus_url))
    log.debug("deploy_zip = {}".format(deploy_zip))

    fileobj = open(deploy_zip, 'rb')
    files = {'file': fileobj}
    try:
        resp = requests.post(nexus_url, files=files)
    except Exception as e:
        log.error("Not valid nexus URL: {}".format(nexus_url))
        log.error(e)
        sys.exit(1)
    finally:
        fileobj.close()

    log.debug("resp.status_code = {}".format(resp.status_code))

    if not str(resp.status_code).startswith('20'):
        log.error("Failed with: {}".format(resp.text))
        zfile = zipfile.ZipFile(deploy_zip)
        log.error(zfile.infolist())
        sys.exit(1)

    url = '{}/service/local/repositories/logs/content-compressed/{}'.format(
        nexus_url, nexus_path)
    r = requests.post(url, files=upload_files)
    log.debug('{}: {}'.format(r.status_code, r.text))

    if r.status_code != 201:
        log.error('Failed to upload to Nexus with status code {}. {}'.format(
            r.status_code, r.content))
        sys.exit(1)
