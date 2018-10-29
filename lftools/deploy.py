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
"""Functions for maintaining staging repositories."""

__author__ = 'Bengt Thuree'

import logging
import re
import sys

from defusedxml.minidom import parseString
import requests

log = logging.getLogger(__name__)


def local_log_error_and_exit(msg1=None, msg2=None):
    """Print error message, and exit."""
    if msg1:
        log.error(msg1)
    if msg2:
        log.error(msg2)
    sys.exit(1)


def local_get_node_from_xml(xml_data, tag_name):
    """Extract tag data from xml data."""
    try:
        dom1 = parseString(xml_data)
        childnode = dom1.getElementsByTagName(tag_name)[0]
    except:
        local_log_error_and_exit("Received bad XML, can not find tag {}".format(tag_name), xml_data)
    return childnode.firstChild.data


def local_format_url(url):
    """Ensure url starts with http and ends with /."""
    start_pattern = re.compile('^(http|https)://')
    if not start_pattern.match(url):
        url = 'http://{}'.format(url)
    if not url.endswith('/'):
        url = '{}/'.format(url)
    return url


def local_request_post(in_url, in_data, in_headers):
    """Execute a request post, return the resp."""
    try:
        resp = requests.post(in_url, data=in_data, headers=in_headers)
    except requests.exceptions.MissingSchema:
        local_log_error_and_exit("Not valid URL: {}".format(in_url))
    except requests.exceptions.ConnectionError:
        local_log_error_and_exit("Could not connect to URL: {}".format(in_url))
    return resp


def nexus_stage_repo_create(nexus_url, staging_profile_id):
    """Create a Nexus staging repo.

    Parameters:
    nexus_url:           URL to Nexus server. (Ex: https://nexus.example.org)
    staging_profile_id:  The staging profile id as defined in Nexus for the
                         staging repo.

    Returns:             staging_repo_id
    """
    nexus_url = '{0}service/local/staging/profiles/{1}/start'.format(
        local_format_url(nexus_url),
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
    resp = local_request_post(nexus_url, xml, headers)

    log.debug("resp.status_code = {}".format(resp.status_code))
    log.debug("resp.text = {}".format(resp.text))

    if re.search('nexus-error', resp.text):
        error_msg = local_get_node_from_xml(resp.text, 'msg')
        if re.search('.*profile with id:.*does not exist.', error_msg):
            local_log_error_and_exit("Staging profile id {} not found.".format(staging_profile_id))
        local_log_error_and_exit(error_msg)

    if resp.status_code == 404:
        local_log_error_and_exit("Did not find nexus site: {}".format(nexus_url))
    if not resp.status_code == 201:
        local_log_error_and_exit("Failed with status code {}".format(resp.status_code), error_msg)

    staging_repo_id = local_get_node_from_xml(resp.text, 'stagedRepositoryId')
    log.debug("staging_repo_id = {}".format(staging_repo_id))

    return staging_repo_id


def nexus_stage_repo_close(nexus_url, staging_profile_id, staging_repo_id):
    """Close a Nexus staging repo.

    Parameters:
    nexus_url:          URL to Nexus server. (Ex: https://nexus.example.org)
    staging_profile_id: The staging profile id as defined in Nexus for the
                        staging repo.
    staging_repo_id:    The ID of the repo to close.
    """
    nexus_url = '{0}service/local/staging/profiles/{1}/finish'.format(
        local_format_url(nexus_url),
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
    resp = local_request_post(nexus_url, xml, headers)

    log.debug("resp.status_code = {}".format(resp.status_code))
    log.debug("resp.text = {}".format(resp.text))

    if re.search('nexus-error', resp.text):
        error_msg = local_get_node_from_xml(resp.text, 'msg')
    else:
        error_msg = resp.text

    if resp.status_code == 404:
        local_log_error_and_exit("Did not find nexus site: {}".format(nexus_url))

    if len(resp.text) > 0:
        if re.search('invalid state: closed', error_msg):
            local_log_error_and_exit("Staging repository is already closed.")
        if re.search('Missing staging repository:', error_msg):
            local_log_error_and_exit("Staging repository do not exist.")
        local_log_error_and_exit('Status Code={}'.format(resp.status_code), error_msg)

    if not resp.status_code == 201:
        local_log_error_and_exit("Failed with status code {}".format(resp.status_code))
