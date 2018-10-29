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
"""Functions for maintaining staging repositories"""

__author__ = 'Bengt Thuree'

import logging
import re
import sys
from defusedxml.minidom import parseString

import requests

log = logging.getLogger(__name__)
# export DEBUG=true


def nexus_stage_repo_close(nexus_url, staging_profile_id, staging_repo_id):
"""Close a Nexus staging repo.
     Parameters:
         nexus_url:          URL to Nexus server. (Ex: https://nexus.example.org)
         staging_profile_id: The staging profile id as defined in Nexus for the
                             staging repo.
         staging_repo_id:    The ID of the repo to close.
"""

    if not nexus_url.startswith('http'):
        nexus_url = 'http://' + nexus_url
    if not nexus_url.endswith('/'):
        nexus_url = nexus_url+'/'

    nexus_url = nexus_url + 'service/local/staging/profiles/' + staging_profile_id + '/finish'

    log.debug("Nexus URL           = %s" % nexus_url)
    log.debug("staging_profile_id  = %s" % staging_profile_id)
    log.debug("staging_repo_id     = %s" % staging_repo_id)

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

    log.debug("resp.status_code = %d, ok=%s" % (resp.status_code, resp.status_code == requests.codes.ok))

    if resp.status_code == 404:
        log.error("Did not find nexus site: {}".format(nexus_url))
        sys.exit(1)

    if len(resp.text) > 0:
        returnXML_dom = parseString(resp.text)
        try:
            errorMsgNode = returnXML_dom.getElementsByTagName('msg')[0]
        except:
            log.error("Failed with status code {}".format(resp.status_code))
            sys.exit(1)

        errorMsg = errorMsgNode.firstChild.data
        if re.search('nexus-error', resp.text):
            if re.search('invalid state: closed', resp.text):
                log.error("This staging repository is already closed. {}".format(errorMsg))
                sys.exit(1)
            if re.search('Missing staging repository:', resp.text):
                log.error("This staging repository do not exist. : {}".format(errorMsg))
                sys.exit(1)

            log.error("{}".format(resp.text))
            sys.exit(1)

    if not resp.status_code == 201:
        log.error("Failed with status code {}".format(resp.status_code))
        sys.exit(1)


def nexus_stage_repo_create(nexus_url, staging_profile_id):
"""Create a Nexus staging repo.
     Parameters:
         nexus_url:  URL to Nexus server. (Ex: https://nexus.example.org)
         staging_profile_id:  The staging profile id as defined in Nexus for the
                              staging repo.

     Returns: staging_repo_id
     """
    if not nexus_url.startswith('http'):
        nexus_url = 'http://' + nexus_url
    if not nexus_url.endswith('/'):
        nexus_url = nexus_url+'/'

    nexus_url = nexus_url + 'service/local/staging/profiles/' + staging_profile_id + '/start'
    log.debug("Nexus URL           = %s" % nexus_url)
    log.debug("staging_profile_id  = %s" % staging_profile_id)

    xml = """
        <promoteRequest>
            <data>
                <description>Create staging repository.</description>
            </data>
        </promoteRequest>
    """
    log.debug("XML code = %s" % xml)

    headers = {'Content-Type': 'application/xml'}  # set what your server accepts
    try:
        resp = requests.post(nexus_url, data=xml, headers=headers)
    except requests.exceptions.MissingSchema:
        log.error("Not valid nexus URL: {}".format(nexus_url))
        sys.exit(1)

    log.debug("resp.status_code = %d, ok=%s" % (resp.status_code, resp.status_code == requests.codes.ok))
    log.debug("resp.text = %s" % resp.text)

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
    log.debug("staging_repo_id = %s" % staging_repo_id)

    return staging_repo_id
