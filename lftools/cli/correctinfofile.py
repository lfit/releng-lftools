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

import click
import ruamel.yaml
import yaml


@click.command()
@click.option('--id', envvar='', type=str, required=True,
              help='lfid of user who created error')
@click.option('--file', envvar='', type=str, required=True,
              help='path to $repo/INFO.yaml')
@click.option('--ldap', envvar='', type=str, required=True,
              help='path to ldap.yaml')
@click.option('--repo', envvar='', type=str, required=False,
              help='repo name')
@click.pass_context
def correctinfofile(ctx, id, file, ldap, repo):
    """Script to insert missing values from ldap into a projects INFO.yaml."""
    ryaml = ruamel.yaml.YAML()
    ryaml.preserve_quotes = True
    ryaml.indent(mapping=4, sequence=6, offset=4)
    ryaml.explicit_start = True
    with open(file, 'r') as stream:
        try:
            yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    data = ryaml.load(open(file))
    data2 = ryaml.load(open(ldap))

    def readfile(data, data2, id):
        committer_info = data['committers']
        repo_info = data['repositories']
        committer_info_ldap = data2['committers']
        readldap(id, ldap, committer_info, committer_info_ldap, repo, repo_info)

    def readldap(id, ldap, committer_info, committer_info_ldap, repo, repo_info):
        for idx, val in enumerate(committer_info_ldap):
            comitter = data2['committers'][idx]['id']
            if comitter == id:
                name = (data2['committers'][idx]['name'])
                email = (data2['committers'][idx]['email'])
                formatid = (data2['committers'][idx]['id'])
                company = (data2['committers'][idx]['company'])
                timezone = (data2['committers'][idx]['timezone'])
            else:
                continue
        getvalues(committer_info, data, id, name, email, formatid, company, timezone, repo, repo_info)

    def getvalues(committer_info, data, id, name, email, formatid, company, timezone, repo, repo_info):
        for idx, val in enumerate(committer_info):
            comitter = data['committers'][idx]['id']
            if comitter == id:
                break
            else:
                continue

        user = ruamel.yaml.comments.CommentedMap(
            (
                ('name', name), ('company', company), ('email', email), ('id', formatid), ('timezone', timezone)
            )
        )
        

        #Not sure how to do the anchors yet
        #d = ruamel.yaml.comments.CommentedMap
        #d.yaml_set_anchor('default')
        #ptland = ("&_%s_ptl" % repo)
        #ptlstar = ("*_%s_ptl" % repo)
        #data['project_lead'] = ptland
        #data['primary_contact'] = ptlstar
        data['project'] = repo
        data['repositories'][0] = repo
        committer_info.append(user)
        f = open(file, 'w')
        ryaml.dump(data, f)
        f.close()

    readfile(data, data2, id)
