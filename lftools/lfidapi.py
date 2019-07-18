#!/usr/bin/env python2
# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2018 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Use the LFIDAPI to add, remove and list members as well as create groups."""

import json
import logging

from email_validator import validate_email
import requests
from six.moves import urllib
import yaml

from lftools.githubhelper import helper_add
from lftools.githubhelper import helper_delete
from lftools.githubhelper import helper_list_minimal
from lftools.oauth2_helper import oauth_helper

log = logging.getLogger(__name__)

PARSE = urllib.parse.urljoin


def check_response_code(response):
    """Response Code Helper function."""
    if response.status_code != 200:
        raise requests.HTTPError("Authorization failed with the following "
                                 "error:\n{}: {}".format(response.status_code,
                                                         response.text))


def helper_check_group_exists(group):
    """List members of a group."""
    access_token, url = oauth_helper()
    url = PARSE(url, group)
    headers = {'Authorization': 'Bearer ' + access_token}
    response = requests.get(url, headers=headers)
    status_code = response.status_code
    return status_code


def helper_search_members(group):
    """List members of a group."""
    access_token, url = oauth_helper()
    url = PARSE(url, group)
    headers = {'Authorization': 'Bearer ' + access_token}
    response = requests.get(url, headers=headers)
    check_response_code(response)
    result = (response.json())
    members = result["members"]
    log.debug(json.dumps(members, indent=4, sort_keys=True))
    return members


def helper_user(user, group, delete):
    """Add and remove users from groups."""
    access_token, url = oauth_helper()
    url = PARSE(url, group)
    headers = {'Authorization': 'Bearer ' + access_token}
    data = {"username": user}
    if delete:
        log.info('Deleting %s from %s' % (user, group))
        response = requests.delete(url, json=data, headers=headers)
    else:
        log.info('Adding %s to %s' % (user, group))
        response = requests.put(url, json=data, headers=headers)
    check_response_code(response)
    result = (response.json())
    log.debug(json.dumps(result, indent=4, sort_keys=True))


def helper_invite(email, group):
    """Email invitation to join group."""
    access_token, url = oauth_helper()
    prejoin = group + '/invite'
    url = PARSE(url, prejoin)
    headers = {'Authorization': 'Bearer ' + access_token}
    data = {"mail": email}
    log.info('Validating email %s' % email)
    if validate_email(email):
        log.info('Inviting %s to join %s' % (email, group))
        response = requests.post(url, json=data, headers=headers)
        check_response_code(response)
        result = (response.json())
        log.debug(json.dumps(result, indent=4, sort_keys=True))
    else:
        log.error("Email '%s' is not valid, not inviting to %s" %
                  (email, group))


def helper_create_group(group):
    """Create group."""
    response_code = helper_check_group_exists(group)
    if response_code == 200:
        log.error("Group %s already exists exiting..." % group)
    else:
        access_token, url = oauth_helper()
        url = '{}/'.format(url)
        headers = {'Authorization': 'Bearer ' + access_token}
        data = {"title": group, "type": "group"}
        log.debug(data)
        log.info('Creating group %s' % group)
        response = requests.post(url, json=data, headers=headers)
        check_response_code(response)
        result = (response.json())
        log.debug(json.dumps(result, indent=4, sort_keys=True))


def helper_match_ldap_to_info(info_file, group, githuborg, noop):
    """Helper only to be used in automation."""
    with open(info_file) as file:
        try:
            info_data = yaml.safe_load(file)
        except yaml.YAMLError as exc:
            print(exc)
    id = 'id'
    if githuborg:
        id = 'github_id'
        ldap_data = helper_list_minimal(githuborg, "test-committers")
    else:
        ldap_data = helper_search_members(group)

    committer_info = info_data['committers']

    info_committers = []
    for count, item in enumerate(committer_info):
        committer = committer_info[count][id]
        info_committers.append(committer)

    ldap_committers = []
    if githuborg:
        for x in ldap_data:
            committer = x
            ldap_committers.append(committer)

    else:
        for count, item in enumerate(ldap_data):
            committer = ldap_data[count]['username']
            ldap_committers.append(committer)

    all_users = ldap_committers + info_committers

    if not githuborg:
        all_users.remove("lfservices_releng")

    log.info("All users in org group")
    all_users = sorted(set(all_users))
    for x in all_users:
        log.info(x)

    for user in all_users:
        removed_by_patch = [item for item in ldap_committers if item not in info_committers]
        if (user in removed_by_patch):
            log.info("%s found in group %s " % (user, group))
            if noop is False:
                log.info("Removing user %s from group %s" % (user, group))
                if githuborg:
                    helper_delete(githuborg, user, group)
                else:
                    helper_user(user, group, "--delete")

        added_by_patch = [item for item in info_committers if item not in ldap_committers]
        if (user in added_by_patch):
            log.info("%s not found in group %s" % (user, group))
            if noop is False:
                log.info("Adding user %s to group %s" % (user, group))
                if githuborg:
                    helper_add(githuborg, user, group)
                else:
                    helper_user(user, group, "")
