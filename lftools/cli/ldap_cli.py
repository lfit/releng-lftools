#!/usr/bin/python
# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""
Generate a CVS of OPNFV Commiters
Prereqs
yum install python-devel openldap-devel, and pip install python-ldap
"""
from __future__ import print_function
import subprocess
import sys
import ldap
import click
import os


#groups = "releng-submitters"
#group = "releng-submitters"

@click.command()
@click.option('--ldapserver', default='ldaps://pdx-wl-lb-lfldap.web.codeaurora.org', envvar='LDAP_SERVER', type=str, required=True)
@click.option('--ldapuserbase', default='ou=Users,dc=freestandards,dc=org', envvar='LDAP_USER_BASE_DN', type=str, required=True)
@click.option('--ldapgroupbase', default='ou=Groups,dc=freestandards,dc=org', envvar='LDAP_GROUP_BASE_DN', type=str, required=True)
@click.option('--ldapsearchscope', default='ldap.SCOPE_SUBTREE', envvar='LDAP_SEARCH_SCOPE', type=str, required=True)
@click.option('--groups', default='foo opnfv-gerrit-releng-submitters', envvar='groups', type=str, required=True)
#@click.option('--groups', default='opnfv-gerrit-releng-submitters,opnfv-gerrit-releng-contributors', envvar='groups')

@click.pass_context
def ldap_cli(ctx, ldapserver, ldapgroupbase, ldapsearchscope, ldapuserbase, groups):
    """Query an Ldap serverx"""
    #ctx.obj['LDAP_SERVER'] = ldapserver
    print("%s" % ldapserver)
    def ldap_connect(ldap_object):
        """
        Start the connection to LDAP
        """
        try:
            ldap_object.protocol_version = ldap.VERSION3
            ldap_object.simple_bind_s()
        except ldap.LDAPError as e:
            if type(e.message) == dict and e.message.has_key('desc'):
                print(e.message['desc'])
            else:
                print(e)
            sys.exit(0)

    def eprint(*args, **kwargs):
        """Print to stderr"""
        print(*args, file=sys.stderr, **kwargs)
    def ldap_disconnect(ldap_object):
        """
        Stop the connnection to LDAP
        """
        ldap_object.unbind_s()

    def ldap_query(ldap_object, dn, search_filter, attrs):
        """
        Perform an LDAP query and return the results
        """
        try:
            ldap_result_id = ldap_object.search(dn, ldapsearchscope, search_filter, attrs)
            result_set = []
            while 1:
                result_type, result_data = ldap_object.result(ldap_result_id, 0)
                if (result_data == []):
                    break
                else:
                    # if you are expecting multiple results you can append them
                    # otherwise you can just wait until the initial result and break out
                    if result_type == ldap.RES_SEARCH_ENTRY:
                        result_set.append(result_data)
            return result_set
        except ldap.LDAPError as e:
            sys.exit(1)

    def package_groups(groups):
        """Package a set of groups from LDIF into a Python dictionary
           containing the groups member uids"""
    group_list = []
    cut_length = len(ldapuserbase)+1
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
        """Covert LDIF user info to CSV of uid,mail,cn"""
        attrs = user[0][0][1]
        return "%s,%s,%s" % (attrs['uid'][0],attrs['cn'][0],attrs['mail'][0])

    def main():
        """Preform an LDAP query"""
        l = ldap.initialize(ldapserver)
        ldap_connect(l)
        for arg in groups[1:2]:
            groups = ldap_query(l, ldapgroupbase, "cn=%s" % arg, ["member"])
            group_dict = package_groups(groups)
            cut_length = len(ldapgroupbase)+1
        for group in group_dict:
            group_name = group['name'][3:-cut_length]
            for user in group['members']:
                user_info = ldap_query(l, ldapgroupbase, user, ["uid", "cn", "mail"])
                try:
                    print("%s," % group_name,user_to_csv(user_info))
                except:
                    eprint("Error parsing user: %s" % user)
                    continue
        ldap_disconnect(l)
    main()


##################################


