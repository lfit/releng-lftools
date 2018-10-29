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
#!/usr/bin/python3

import logging
import requests
import re
import sys
import xml.dom.minidom


# remove shell script from shell/deploy
# modify lftools/cli/deploy.py also
#         nexuscmd.nexus_stage_repo_close(nexus_url,
#                                         staging_profile_id,
#                                         staging_repo_id)
#     nexus.add_command(nexus_stage_repo_close)
#
# Put script in lftools/nexus/cmd.py

def nexus_stage_repo_close(nexus_url, staging_profile_id, staging_repo_id):

    # Closes a Nexus staging repo
    #
    # Parameters:
    #     nexus_url:          URL to Nexus server. (Ex: https://nexus.example.org)
    #     staging_profile_id: The staging profile id as defined in Nexus for the
    #                         staging repo.
    #     staging_repo_id:    The ID of the repo to close.

    ## Add '/' to url if not there already.
    if not nexus_url.endswith('/'):
    nexus_url=nexus_url+'/'

    logger.debug ("Nexus URL before    = %s" % nexus_url)
    nexus_url=nexus_url + '/service/local/staging/profiles/' + staging_profile_id + '/finish'
    logger.debug ("Nexus URL after     = %s" % nexus_url)

    logger.debug ("staging_profile_id  = %s" % staging_profile_id)
    logger.debug ("staging_repo_id     = %s" % staging_repo_id)

    # Prepare XML statement to close staging repo
    xml = """
        <promoteRequest>
            <data>
                <stagedRepositoryId>$staging_repo_id</stagedRepositoryId>
                <description>Close staging repository.</description>
            </data>
        </promoteRequest>
    """
    logger.debug ("XML code = %s" % xml)

    # Send the Request command
    headers = {'Content-Type': 'application/xml'} # set what your server accepts
    resp = requests.post(nexus_url, data=xml, headers=headers)
    logger.debug ( "resp.status_code = %d, ok=%s" % (resp.status_code, resp.status_code == requests.codes.ok))
    logger.debug ( "resp.text = %s" % resp.text)

    # If error, report it, and exit
    if re.search(resp.text, 'nexus-error'):
        sys.exit ("ERROR: %s" % resp.text)
    else:
        if not resp.status_code = 201:
            sys.exit ("ERROR: Failed with status code %s" % resp.status_code)


def nexus_stage_repo_create(nexus_url, staging_profile_id):

    # Create a Nexus staging repo
    #
    # Parameters:
    #     nexus_url:  URL to Nexus server. (Ex: https://nexus.example.org)
    #     staging_profile_id:  The staging profile id as defined in Nexus for the
    #                          staging repo.
    #
    # Returns: staging_repo_id

    ## Add '/' to url if not there already.
    if not nexus_url.endswith('/'):
        nexus_url=nexus_url+'/'

    logger.debug ("Nexus URL before    = %s" % nexus_url)
    nexus_url=nexus_url + '/service/local/staging/profiles/' + staging_profile_id + '/start'
    logger.debug ("Nexus URL after     = %s" % nexus_url)
    logger.debug ("staging_profile_id  = %s" % staging_profile_id)

    # Prepare XML statement to close staging repo
    xml = """
        <promoteRequest>
            <data>
                <description>Create staging repository.</description>
            </data>
        </promoteRequest>
    """
    logger.debug ("XML code = %s" % xml)

    # Send the Request command
    headers = {'Content-Type': 'application/xml'} # set what your server accepts
    resp = requests.post(nexus_url, data=xml, headers=headers)
    logger.debug ( "resp.status_code = %d, ok=%s" % (resp.status_code, resp.status_code == requests.codes.ok))
    logger.debug ( "resp.text = %s" % resp.text)

    # If error, report it, and exit
    if re.search(resp.text, 'nexus-error'):
        sys.exit ("ERROR: %s" % resp.text)
    else:
        if not resp.status_code = 201:
            sys.exit ("ERROR: Failed with status code %s" % resp.status_code)

    # Now we need to parse the XML resp, and fetch the value for stagedRepositoryId
    dom = xml.dom.minidom.parseString(resp.text)
    childnode = dom.getElementsByTagName('stagedRepositoryId')[0]
    staging_repo_id = childnode.firstChild.data
    logger.debug ("staging_repo_id = %s" % staging_repo_id)

    return staging_repo_id
