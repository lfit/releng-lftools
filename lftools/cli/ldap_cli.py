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
"""Generate a CSV of a Projects Commiters.

Prereqs:
- yum install python-devel openldap-devel
- pip install python-ldap
"""

from __future__ import print_function

import subprocess
import sys

import click

import ldap


@click.group()
@click.pass_context
def ldap_cli(ctx):
    """LDAP TOOLS."""
    pass


@click.command()
@click.argument('group')
@click.pass_context
def yaml4info(ctx, group):
    """Build yaml of committers for your INFO.yaml."""
    status = subprocess.call(['yaml4info', group])
    sys.exit(status)


@click.command()
@click.argument('gerrit_url')
@click.argument('group')
@click.pass_context
def inactivecommitters(ctx, gerrit_url, group):
    """Check committer participation."""
    status = subprocess.call(['inactivecommitters', gerrit_url, group])
    sys.exit(status)


@click.command()
@click.argument('gerrit_clone_base')
@click.argument('ldap_group')
@click.argument('repo')
@click.option('--purpose', envvar='purpose', type=str,
              help='Must be one of READY_FOR_INFO LINT IN-REVIEW')
@click.option('--review', type=str, required=False,
              help='review number in gerrit, required if purpose is IN-REVIEW')
@click.pass_context
def autocorrectinfofile(ctx, gerrit_clone_base, ldap_group, repo, purpose, review):
    """Verify INFO.yaml against LDAP group.\n
    PURPOSE must be one of: READY_FOR_INFO LINT IN-REVIEW\n
    GERRITCLONEBASE must be a url: https://gerrit.opnfv.org/gerrit/\n
    """
    params = ['autocorrectinfofile']
    params.extend([gerrit_clone_base, ldap_group, repo])
    if purpose:
        params.extend([purpose])
    if review:
        params.extend([review])
    status = subprocess.call(params)
    sys.exit(status)


@click.command()
@click.option('--ldap-server', default='ldaps://pdx-wl-lb-lfldap.web.codeaurora.org',
              envvar='LDAP_SERVER', type=str, required=True)
@click.option('--ldap-user-base', default='ou=Users,dc=freestandards,dc=org',
              envvar='LDAP_USER_BASE_DN', type=str, required=True)
@click.option('--ldap-group-base', default='ou=Groups,dc=freestandards,dc=org',
              envvar='LDAP_GROUP_BASE_DN', type=str, required=True)
@click.argument('groups')
@click.pass_context
def csv(ctx, ldap_server, ldap_group_base, ldap_user_base, groups):
    """Query an Ldap server."""
    # groups needs to be a list
    groups = groups.split(' ')

    def ldap_connect(ldap_object):
        """Start the connection to LDAP."""
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
        """Print to stderr."""
        print(*args, file=sys.stderr, **kwargs)

    def ldap_disconnect(ldap_object):
        """Stop the connnection to LDAP."""
        ldap_object.unbind_s()

    def ldap_query(ldap_object, dn, search_filter, attrs):
        """Perform an LDAP query and return the results."""
        try:
            ldap_result_id = ldap_object.search(dn, ldap.SCOPE_SUBTREE, search_filter, attrs)
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
        """Package a set of groups from LDIF into a Python dictionary.

        containing the groups member uids.
        """
        group_list = []
        cut_length = len(ldap_user_base)+1
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
        """Covert LDIF user info to CSV of uid,mail,cn."""
        attrs = user[0][0][1]
        return ",".join([attrs['uid'][0], attrs['cn'][0], attrs['mail'][0]])

    def main(groups):
        """Preform an LDAP query."""
        l = ldap.initialize(ldap_server)
        ldap_connect(l)
        for arg in groups:
            groups = ldap_query(l, ldap_group_base, "cn=%s" % arg, ["member"])
            group_dict = package_groups(groups)
            cut_length = len(ldap_group_base)+1
            for group_bar in group_dict:
                group_name = group_bar['name'][3:-cut_length]
                for user in group_bar['members']:
                    user_info = ldap_query(l, ldap_user_base, user, ["uid", "cn", "mail"])
                    try:
                        print("%s,%s" % (group_name, user_to_csv(user_info)))
                    except:
                        eprint("Error parsing user: %s" % user)
                        continue
        ldap_disconnect(l)
    main(groups)


ldap_cli.add_command(csv)
ldap_cli.add_command(inactivecommitters)
ldap_cli.add_command(yaml4info)
ldap_cli.add_command(autocorrectinfofile)
