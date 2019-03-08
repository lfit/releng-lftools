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

from email_validator import validate_email
import requests
from six.moves import urllib
import yaml

from lftools.oauth2_helper import oauth_helper

PARSE = urllib.parse.urljoin


def check_response_code(response):
    """Response Code Helper function."""
    if response.status_code != 200:
        raise requests.HTTPError("Authorization failed with the following "
                                 "error:\n{}: {}".format(response.status_code,
                                                         response.text))


def helper_search_members(group):
    """List members of a group."""
    access_token, url = oauth_helper()
    url = PARSE(url, group)
    headers = {'Authorization': 'Bearer ' + access_token}
    response = requests.get(url, headers=headers)
    check_response_code(response)
    result = (response.json())
    members = result["members"]
    print(json.dumps(members, indent=4, sort_keys=True))
    return members


def helper_user(user, group, delete):
    """Add and remove users from groups."""
    access_token, url = oauth_helper()
    url = PARSE(url, group)
    headers = {'Authorization': 'Bearer ' + access_token}
    data = {"username": user}
    if delete:
        response = requests.delete(url, json=data, headers=headers)
    else:
        response = requests.put(url, json=data, headers=headers)
    check_response_code(response)
    result = (response.json())
    print(json.dumps(result, indent=4, sort_keys=True))


def helper_invite(email, group):
    """Email invitation to join group."""
    access_token, url = oauth_helper()
    prejoin = group + '/invite'
    url = PARSE(url, prejoin)
    headers = {'Authorization': 'Bearer ' + access_token}
    data = {"mail": email}
    print('Validating email', email)
    if validate_email(email):
        response = requests.post(url, json=data, headers=headers)
        check_response_code(response)
        result = (response.json())
        print(json.dumps(result, indent=4, sort_keys=True))
    else:
        print("Email is not valid")


def helper_create_group(group):
    """Create group."""
    access_token, url = oauth_helper()
    url = '{}/'.format(url)
    headers = {'Authorization': 'Bearer ' + access_token}
    data = {"title": group, "type": "group"}
    print(data)
    response = requests.post(url, json=data, headers=headers)
    check_response_code(response)
    result = (response.json())
    print(json.dumps(result, indent=4, sort_keys=True))


def helper_match_ldap_to_info(info_file, group, noop):
    """Helper only to be used in automation."""
    with open(info_file) as file:
        try:
            info_data = yaml.safe_load(file)
        except yaml.YAMLError as exc:
            print(exc)

    ldap_data = helper_search_members(group)
    committer_info = info_data['committers']

    info_committers = []
    for count, item in enumerate(committer_info):
        committer = committer_info[count]['id']
        info_committers.append(committer)

    ldap_committers = []
    for count, item in enumerate(ldap_data):
        committer = ldap_data[count]['username']
        ldap_committers.append(committer)

    all_users = ldap_committers + info_committers
    all_users.remove("lfservices_releng")
    all_users = sorted(set(all_users))

    for user in all_users:
        removed_by_patch = [item for item in ldap_committers if item not in info_committers]
        if (user in removed_by_patch):
            print(" {} found in group {} ".format(user, group))
            if noop is False:
                print(" removing user {} from group {}".format(user, group))
                helper_user(user, group, "--delete")

        added_by_patch = [item for item in info_committers if item not in ldap_committers]
        if (user in added_by_patch):
            print(" {} not found in group {} ".format(user, group))
            if noop is False:
                print(" adding user {} to group {}".format(user, group))
                helper_user(user, group, "")
