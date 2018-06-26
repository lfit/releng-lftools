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
"""Script to insert missing values from ldap into a projects INFO.yaml."""

import click
import ruamel.yaml
import yaml


@click.group()
@click.pass_context
def infofile(ctx):
    """INFO.yaml TOOLS."""
    pass


@click.command()
@click.argument('file', envvar='FILE_NAME', required=True)
@click.option('--full', type=bool, required=False,
              help='Output name email and id for all committers in an infofile')
@click.option('--id', type=str, required=False,
              help='Full output for a specific LIFD')
@click.pass_context
def parse(ctx, file, full, id):
    """Extract Committer info from INFO.yaml or LDAP dump."""
    with open(file, 'r') as yaml_file:
        project = yaml.safe_load(yaml_file)

    def list_committers(full, id, project):
        """List commiters from the INFO.yaml file."""
        lookup = project.get('committers', [])

        for item in lookup:
            if full and id:
                print("full and id are mutially exclusive")
                exit()
            elif full:
                print("    - name: '%s'" % item['name'])
                print("      email: '%s'" % item['email'])
                print("      id: '%s'" % item['id'])
            elif id and item['id'] == (id):
                print("    - name: '%s'" % item['name'])
                print("      email: '%s'" % item['email'])
                print("      id: '%s'" % item['id'])
            elif not full and not id:
                print("      id: '%s'" % item['id'])

    list_committers(full, id, project)


@click.command()
@click.argument('info_file')
@click.argument('ldap_file')
@click.argument('id')
@click.option('--repo', type=str, required=False,
              help='repo name')
@click.pass_context
def correct(ctx, id, info_file, ldap_file, repo):
    """Script to insert missing values from ldap into a projects INFO.yaml."""
    ryaml = ruamel.yaml.YAML()
    ryaml.preserve_quotes = True
    ryaml.indent(mapping=4, sequence=6, offset=4)
    ryaml.explicit_start = True
    with open(info_file, 'r') as stream:
        try:
            yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    info_data = ryaml.load(open(info_file))
    ldap_data = ryaml.load(open(ldap_file))

    def readfile(data, ldap_data, id):
        committer_info = info_data['committers']
        repo_info = info_data['repositories']
        committer_info_ldap = ldap_data['committers']
        readldap(id, ldap_file, committer_info, committer_info_ldap, repo, repo_info)

    def readldap(id, ldap_file, committer_info, committer_info_ldap, repo, repo_info):
        for idx, val in enumerate(committer_info):
            committer = info_data['committers'][idx]['id']
            if committer == id:
                print('{} is alread in {}'.format(id, info_file))
                exit()

        for idx, val in enumerate(committer_info_ldap):
            committer = ldap_data['committers'][idx]['id']
            if committer == id:
                name = (ldap_data['committers'][idx]['name'])
                email = (ldap_data['committers'][idx]['email'])
                formatid = (ldap_data['committers'][idx]['id'])
                company = (ldap_data['committers'][idx]['company'])
                timezone = (ldap_data['committers'][idx]['timezone'])
        try:
            name
        except NameError:
            print('{} does not exist in {}'.format(id, ldap_file))
            exit()

        user = ruamel.yaml.comments.CommentedMap(
            (
                ('name', name), ('company', company), ('email', email), ('id', formatid), ('timezone', timezone)
            )
        )

        info_data['repositories'][0] = repo
        committer_info.append(user)

        with open(info_file, 'w') as f:
            ryaml.dump(info_data, f)

    readfile(info_data, ldap_data, id)


infofile.add_command(parse)
infofile.add_command(correct)
