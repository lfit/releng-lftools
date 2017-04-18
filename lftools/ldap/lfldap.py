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
"""Library for creating identies and groups with LDAP."""

__author__ = 'Anil Belur'

import yaml

import ldap


def create_ldap_groups_ids(config_file, settings_file):
    """Create LDAP groups and identies for ODL.

    Creates a LDAP project group and adds initial committers
    to the group. LDAP server settings are read from settings.yaml and
    project creattion configuration is read from config.yaml

    :arg str config_file: Project config file on project and member heirarchy.
    :arg str settings_file: Config file containing ODL LDAP administrative settings.
    """
    # open our settings file
    f = open(settings_file, 'r')
    settings = yaml.load(f)
    f.close()

    # open our config file
    f = open(config_file, 'r')
    config = yaml.load(f)
    f.close()

    error = False
    if not 'ldap' in config:
        print('ERROR: ldapurl needs to be defined')
        error = True

    if not 'groups_base' in config['ldap']:
        print('ERROR: LDAP project group base dn needs to be defined')
        error = True

    if not 'users_base' in config['ldap']:
        print('ERROR: LDAP users base dn needs to be defined')
        error = True

    if not 'project_name' in config['ldap']:
        print('ERROR: project name needs to be defined')
        error = True

    if not 'members' in config['ldap']:
        print('ERROR: list of members needs to be defined')
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
