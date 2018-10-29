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


def local_format_url(url):
    """Ensure url starts with http and ends with /."""
    start_pattern = re.compile('^(http|https)://')
    if not start_pattern.match(url):
        url = 'http://{}'.format(url)
    if not url.endswith('/'):
        url = '{}/'.format(url)
    return url


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

    headers = {'Content-Type': 'application/xml'}  # set what your server accepts
    try:
        resp = requests.post(nexus_url, data=xml, headers=headers)
    except requests.exceptions.MissingSchema:
        log.error("Not valid nexus URL: {}".format(nexus_url))
        sys.exit(1)

    log.debug("resp.status_code = {}".format(resp.status_code))

    if resp.status_code == 404:
        log.error("Did not find nexus site: {}".format(nexus_url))
        sys.exit(1)

    if len(resp.text) > 0:
        returnXML_dom = parseString(resp.text)
        try:
            error_msg_node = returnXML_dom.getElementsByTagName('msg')[0]
        except:
            log.error("Failed with status code {}".format(resp.status_code))
            sys.exit(1)

        error_msg = error_msg_node.firstChild.data
        if re.search('nexus-error', resp.text):
            if re.search('invalid state: closed', resp.text):
                log.error("This staging repository is already closed. {}".format(error_msg))
                sys.exit(1)
            if re.search('Missing staging repository:', resp.text):
                log.error("This staging repository do not exist. : {}".format(error_msg))
                sys.exit(1)

            log.error("{}".format(resp.text))
            sys.exit(1)

    if not resp.status_code == 201:
        log.error("Failed with status code {}".format(resp.status_code))
        sys.exit(1)


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

    headers = {'Content-Type': 'application/xml'}  # set what your server accepts
    try:
        resp = requests.post(nexus_url, data=xml, headers=headers)
    except requests.exceptions.MissingSchema:
        log.error("Not valid nexus URL: {}".format(nexus_url))
        sys.exit(1)

    log.debug("resp.status_code = {}".format(resp.status_code))
    log.debug("resp.text = {}".format(resp.text))

    if resp.status_code == 404:
        log.error("Did not find nexus site: {}".format(nexus_url))
        sys.exit(1)
    if re.search('nexus-error', resp.text):
        log.error("{}".format(resp.text))
        sys.exit(1)
    else:
        if not resp.status_code == 201:
            sys.exit("Failed with status code {}".format(resp.status_code))
            sys.exit(1)

    # Now we need to parse the XML resp, and fetch the value for stagedRepositoryId
    try:
        dom1 = parseString(resp.text)
        childnode = dom1.getElementsByTagName('stagedRepositoryId')[0]
    except:
        log.error("Weird. Staging Repository created, but got bad XML {}".format(resp.text))
        sys.exit(1)

    staging_repo_id = childnode.firstChild.data
    log.debug("staging_repo_id = {}".format(staging_repo_id))

    return staging_repo_id
