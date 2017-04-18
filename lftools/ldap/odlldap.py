# -*- code: utf-8 -*-
# @License EPL-1.0 <http://spdx.org/licenses/EPL-1.0>
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
# vim: sw=4 ts=4 sts=4 et :


"""Library for creating identies and groups with LDAP."""

__author__ = 'Anil Belur'

""" Create LDAP project group and add initial committers.

    This script creates a LDAP project group and adds initial committers
    to the group. LDAP server settings are read from settings.yaml and
    project creattion configuration is read from config.yaml

    usage: ldap_create_project.py
    ex:
        ldap_create_project.py -s settings.yaml -c config.yaml
"""

import logging
import sys
import ldap
#import ldap.modlist as modlist
import yaml


def create_ldap_groups_ids(config_file, settings_file):

    if not settings_file:
        sys.exit('Settings file is required')

    if not config_file:
        sys.exit('Config file is required')

    # open our settings file
    f = open(settings_file, 'r')
    settings = yaml.load(f)
    f.close()

    error = False
    if not 'ldap' in settings:
        print 'ldap needs to be defined'
        error = True

    if not 'admin_dn' in settings:
        print 'LDAP admin_dn needs to be defined'
        error = True

    if not 'password' in settings:
        print 'password needs to be defined'
        error = True

    if error:
        sys.exit(1)

    # open our config file
    f = open(config_file, 'r')
    config = yaml.load(f)
    f.close()

    error = False
    if not 'ldap' in config:
        print 'ldapurl needs to be defined'
        error = True

    if not 'groups_base' in config['ldap']:
        print 'LDAP project group base dn needs to be defined'
        error = True

    if not 'users_base' in config['ldap']:
        print 'LDAP users base dn needs to be defined'
        error = True

    if not 'project_name' in config['ldap']:
        print 'project name needs to be defined'
        error = True

    if not 'members' in config['ldap']:
        print 'list of members needs to be defined'
        error = True

    if error:
        sys.exit(1)

    print("Connecting to LDAP Server:" + settings['ldap'])

    try:
        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
        l = ldap.initialize(str(settings['ldap']))
        l.set_option(ldap.OPT_REFERRALS, 0)
        l.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
        l.set_option(ldap.OPT_X_TLS, ldap.OPT_X_TLS_DEMAND)
        l.set_option(ldap.OPT_X_TLS_DEMAND, True)
        l.set_option(ldap.OPT_DEBUG_LEVEL, 255)
        l.simple_bind(settings['admin_dn'], settings['password'])

        # The dn of our new entry/object
        dn = "cn=gerrit-" + str(config['ldap']['project_name']) + \
             "-committers," + str(config['ldap']['groups_base'])

        # Use dict to help build the "body" of the object
        attrs = {}
        attrs['objectclass'] = ['top', 'groupOfNames']
        attrs['cn'] = "gerrit-" + str(config['ldap']['project_name']) + "-committers"
        member_list = []
        for id in config['ldap']['members']:
            member = "uid=" + str(id) + "," + str(config['ldap']['users_base'])
            member_list.append(member)
            print("Add member: " + member + " to group: " + attrs['cn'])
        attrs['member'] = member_list

        # Convert our dict to ldif syntax using modlist-module
        ldif = ldap.modlist.addModlist(attrs)

        # Do the actual synchronous add-operation to the ldapserver
        l.add_s(dn, ldif)

        # close the bind op
        l.unbind_s()
        print("Done")
    except ldap.LDAPError as e:
        print e
