#!/usr/bin/env python2
# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Script to insert missing values from ldap into a projects INFO.yaml."""

from cStringIO import StringIO
from pathlib import Path
from collections import OrderedDict

import click
import collections
import ruamel.yaml
import sys
import yaml

@click.command()
@click.option('--id', envvar='', type=str, required=True,
              help='lfid of user who created error')
@click.option('--file', envvar='', type=str, required=True,
              help='path to $repo/INFO.yaml')
@click.option('--ldap', envvar='', type=str, required=True,
              help='path to ldap.yaml')
@click.pass_context

def correctinfofile(ctx, id, file, ldap):
    """Script to insert missing values from ldap into a projects INFO.yaml.""" 
    ryaml = ruamel.yaml.YAML()
    ryaml.preserve_quotes = True
    ryaml.indent(mapping=4, sequence=6, offset=4)
    ryaml.explicit_start = True
    data = ryaml.load(open(file))
    data2 = ryaml.load(open(ldap))

    #assert buf.getvalue() == yaml.load(open(file_name))

    def readfile(data, data2, id):
        committer_info = data['committers']
        committer_info_ldap = data2['committers']
        readldap(id, ldap, committer_info, committer_info_ldap)

    def readldap(id, ldap, committer_info, committer_info_ldap):
        for idx, val in enumerate(committer_info_ldap):
            comitter = data2['committers'][idx]['id']
            if comitter == id:
                name = (data2['committers'][idx]['name'])
                email = (data2['committers'][idx]['email'])
                formatid = (data2['committers'][idx]['id'])
            else:
                continue
        getvalues(committer_info, data, id, name, email, formatid)


    def getvalues(committer_info, data, id, name, email, formatid):
        for idx, val in enumerate(committer_info):
            comitter = data['committers'][idx]['id']
            if comitter == id:
                break
            else:
                continue


        #formatid = "'{}'".format(id)
        #data['foo'] = SingleQuotedScalarString('bar')

        user = ruamel.yaml.comments.CommentedMap(
                (
                    ('name', name), ('email', email), ('id', formatid)
                    )
                )
        committer_info.append(user)
        f = open(file,'w')
        ryaml.dump(data, f)
        buf = StringIO()
        ryaml.dump(data, buf)
        f.close()

    readfile(data, data2, id)
