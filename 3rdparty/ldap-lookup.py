#!/usr/bin/python
# SPDX-license-identifier: Apache-2.0
##############################################################################
# Copyright (c) 2016 Linux Foundation and others.
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

"""
Generate a CVS of OPNFV Commiters
Prereqs
yum install python-devel openldap-devel, and pip install python-ldap
"""
from __future__ import print_function

import ldap
import sys


LDAP_SERVER="ldaps://pdx-wl-lb-lfldap.web.codeaurora.org"
LDAP_USER_BASE_DN="ou=Users,dc=freestandards,dc=org"
LDAP_GROUP_BASE_DN="ou=Groups,dc=freestandards,dc=org"
LDAP_SEARCH_SCOPE = ldap.SCOPE_SUBTREE

def eprint(*args, **kwargs):
    """Print to stderr"""
    print(*args, file=sys.stderr, **kwargs)

def ldap_connect(ldap_object):
    """
    Start the connection to LDAP
    """
    try:
        ldap_object.protocol_version = ldap.VERSION3
        ldap_object.simple_bind_s()
    except ldap.LDAPError, e:
      if type(e.message) == dict and e.message.has_key('desc'):
          print(e.message['desc'])
      else:
          print(e)
      sys.exit(0)
    eprint("> Successfully connected to LDAP")

def ldap_disconnect(ldap_object):
    """
    Stop the connnection to LDAP
    """
    ldap_object.unbind_s()
    #eprint("> Disconnnected from LDAP")

def ldap_query(ldap_object, dn, search_filter, attrs):
    """
    Perform an LDAP query and return the results
    """
    try:
        ldap_result_id = ldap_object.search(dn, LDAP_SEARCH_SCOPE, search_filter, attrs)
        result_set = []
        while 1:
            result_type, result_data = ldap_object.result(ldap_result_id, 0)
            if (result_data == []):
                break
            else:
                ## if you are expecting multiple results you can append them
                ## otherwise you can just wait until the initial result and break out
                if result_type == ldap.RES_SEARCH_ENTRY:
                    result_set.append(result_data)
        return result_set
    except ldap.LDAPError, e:
        #eprint(e)
        sys.exit(1)

def package_groups(groups):
    """Package a set of groups from LDIF into a Python dictionary
       containing the groups member uids"""
    group_list = []
    cut_length=len(LDAP_USER_BASE_DN)+1
    for group in groups:
       group_d = dict(name=group[0][0])
       members = []
       for group_attrs in group:
           for member in group_attrs[1]['member']:
               members.append(member[:-cut_length])
       group_d['members'] = members
       group_list.append(group_d)
    return group_list

def user_to_csv(user):
    """Covert LDIF user info to CSV of mail, cn"""
    attrs = user[0][0][1]
    return "%s %s" % (attrs['cn'][0],attrs['mail'][0])

def main():
    """Preform an LDAP query"""
    l = ldap.initialize(LDAP_SERVER)
    ldap_connect(l)

    for arg in sys.argv[1:2]:
       #groups = ldap_query(l, LDAP_GROUP_BASE_DN, "cn=opnfv-gerrit-*", ["member"])
        groups = ldap_query(l, LDAP_GROUP_BASE_DN, "cn=%s" % arg, ["member"])
        group_dict = package_groups(groups)
        cut_length=len(LDAP_GROUP_BASE_DN)+1

    for group in group_dict:
        group_name = group['name'][3:-cut_length]
        #print("\n%s" % group_name)
        #eprint("> Processing: %s" % group_name)
        for user in group['members']:
            user_info = ldap_query(l, LDAP_USER_BASE_DN, user, ["mail", "cn"])
            try:
                print("%s" % group_name, user_to_csv(user_info))
#                print(user_to_csv(user_info))
                #print (user_info)
            except:
                eprint("Error parsing user: %s" % user)
                continue

    ldap_disconnect(l)

if __name__ == "__main__":
  main()
