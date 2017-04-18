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

import sys

import yaml

import ldap
import ldap.modlist as modlist


def create_ldap_groups_ids(config_file, settings_file):
    """Create LDAP groups.

    Creates a LDAP project group and adds initial committers
    to the group. LDAP server settings are read from settings.yaml and
    project creation configuration is read from config.yaml

    :arg str config_file: Project config file on project and member heirarchy
    :arg str settings_file: Config file containing LDAP administrative settings
    """
    # open our settings file
    with open(settings_file, 'r') as f:
        settings = yaml.load(f)

    # open our config file
    with open(config_file, 'r') as f:
        config = yaml.load(f)

    required_fields = [
        'groups_base',
        'users_base',
        'project_name',
        'master_project',
        'members',
    ]

    for field in required_fields:
        if field not in config['ldap']:
            print('ERROR: {} needs to be defined.'.format(field))
            sys.exit(1)

    print("Connecting to LDAP Server: {}".format(settings['ldap']))

    try:
        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
        ldapcon = ldap.initialize(str(settings['ldap']))
        ldapcon.set_option(ldap.OPT_REFERRALS, 0)
        ldapcon.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
        ldapcon.set_option(ldap.OPT_X_TLS, ldap.OPT_X_TLS_DEMAND)
        ldapcon.set_option(ldap.OPT_X_TLS_DEMAND, True)
        ldapcon.set_option(ldap.OPT_DEBUG_LEVEL, 255)
        ldapcon.simple_bind(settings['admin_dn'], settings['password'])

        # The dn of our new entry/object
        dn = "cn={}-gerrit-{}-committers,{}".format(
             str(config['ldap']['master_project']),
             str(config['ldap']['project_name']),
             str(config['ldap']['groups_base']))


        # Use dict to help build the "body" of the object
        attrs = {}
        attrs['objectclass'] = ['top', 'groupOfNames']
        attrs['cn'] = "{}-gerrit-{}-committers".format(
                      str(config['ldap']['master_project']),
                      str(config['ldap']['project_name']))
        member_list = []
        for id in config['ldap']['members']:
            member = "uid={},{}".format(str(id),
                                        str(config['ldap']['users_base']))
            member_list.append(member)
            print('Add member: {} to group: {}'.format(member, attrs['cn']))
        attrs['member'] = member_list

        # Convert our dict to ldif syntax using modlist-module
        ldif = modlist.addModlist(attrs)

        # Do the actual synchronous add-operation to the ldapserver
        ldapcon.add_s(dn, ldif)

        # close the bind op
        ldapcon.unbind_s()
        print('Done')
    except ldap.LDAPError as e:
        print('Error: {}'.format(str(e)))
