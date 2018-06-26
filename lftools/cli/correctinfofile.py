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
"""Script to modify INFO.yaml or send invites."""


import sys
import click
import yaml
import ruamel.yaml
from cStringIO import StringIO
import collections
from pathlib import Path
#from ruamel.yaml.util import load_yaml_guess_indent
#from ruamel.yaml.scalarstring import SingleQuotedScalarString, DoubleQuotedScalarString
from collections import OrderedDict
#from ruamel.yaml import YAML

@click.command()
@click.option('--id', envvar='', type=str, required=True,
              help='lfid of user who created error')
@click.option('--file', envvar='', type=str, required=False,
              help='path to $repo/INFO.yaml')
@click.option('--ldap', envvar='', type=str, required=False,
              help='path to ldap.yaml')
@click.pass_context

def correctinfofile(ctx, id, file, ldap):

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
                print('no user found')
        getvalues(committer_info, data, id, name, email, formatid)


    def getvalues(committer_info, data, id, name, email, formatid):
        for idx, val in enumerate(committer_info):
            comitter = data['committers'][idx]['id']
            if comitter == id:
                break
            else:
                print('no user found')


        #formatid = "'{}'".format(id)
        #data['foo'] = SingleQuotedScalarString('bar')

        user = ruamel.yaml.comments.CommentedMap(
                (
                    ('name', name), ('email', email), ('id', formatid)
                    )
                )
        committer_info.append(user)

        ryaml.dump(data, sys.stdout)
        buf = StringIO()
        ryaml.dump(data, buf)

    readfile(data, data2, id)
