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

import logging
import os
import re
import shutil
import sys

from defusedxml.minidom import parseString
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


def _get_node_from_xml(xml_data, tag_name):
    """Extract tag data from xml data."""
    try:
        dom1 = parseString(xml_data)
        childnode = dom1.getElementsByTagName(tag_name)[0]
    except:
        _log_error_and_exit("Received bad XML, can not find tag {}".format(tag_name), xml_data)
    return childnode.firstChild.data


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
