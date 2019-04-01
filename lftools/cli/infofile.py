#!/usr/bin/env python2
# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Script to insert missing values from ldap into a projects INFO.yaml."""

import logging
import sys

import click
from pygerrit2 import GerritRestAPI
import ruamel.yaml
import yaml

log = logging.getLogger(__name__)


@click.group()
@click.pass_context
def infofile(ctx):
    """INFO.yaml TOOLS."""
    pass


@click.command(name='get-committers')
@click.argument('file', envvar='FILE_NAME', required=True)
@click.option('--full', type=bool, required=False,
              help='Output name email and id for all committers in an infofile')
@click.option('--id', type=str, required=False,
              help='Full output for a specific LFID')
@click.pass_context
def get_committers(ctx, file, full, id):
    """Extract Committer info from INFO.yaml or LDAP dump."""
    with open(file, 'r') as yaml_file:
        project = yaml.safe_load(yaml_file)

    def print_committer_info(committer, full):
        if full:
            print("    - name: {}".format(committer['name']))
            print("      email: {}".format(committer['email']))
        print("      id: {}".format(committer['id']))

    def list_committers(full, id, project):
        """List commiters from the INFO.yaml file."""
        lookup = project.get('committers', [])

        for item in lookup:
            if id:
                if item['id'] == id:
                    print_committer_info(item, full)
                    break
                else:
                    continue
            print_committer_info(item, full)

    list_committers(full, id, project)


@click.command(name='sync-committers')
@click.argument('info_file')
@click.argument('ldap_file')
@click.argument('id')
@click.option('--repo', type=str, required=False,
              help='repo name')
@click.pass_context
def sync_committers(ctx, id, info_file, ldap_file, repo):
    """Sync committer information from LDAP into INFO.yaml."""
    ryaml = ruamel.yaml.YAML()
    ryaml.preserve_quotes = True
    ryaml.indent(mapping=4, sequence=6, offset=4)
    ryaml.explicit_start = True
    with open(info_file, 'r') as stream:
        try:
            yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    with open(info_file) as f:
        info_data = ryaml.load(f)
    with open(ldap_file) as f:
        ldap_data = ryaml.load(f)

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


@click.command(name='check-votes')
@click.argument('info_file')
@click.argument('gerrit_url')
@click.argument('change_number')
@click.option('--tsc', type=str, required=False,
              help='path to TSC INFO file')
@click.pass_context
def check_votes(ctx, info_file, gerrit_url, change_number, tsc):
    """Check votes on an INFO.yaml change.

    Check for Majority of votes on a gerrit patchset
    which changes an INFO.yaml file.
    """
    def main(ctx, info_file, gerrit_url, change_number, tsc, majority_of_committers):
        """Function so we can iterate into TSC members after commiter vote has happend."""
        with open(info_file) as file:
            try:
                info_data = yaml.safe_load(file)
            except yaml.YAMLError as exc:
                log.error(exc)

        committer_info = info_data['committers']

        info_committers = []
        for count, item in enumerate(committer_info):
            committer = committer_info[count]['id']
            info_committers.append(committer)

        rest = GerritRestAPI(url=gerrit_url)
        changes = rest.get("changes/{}/reviewers".format(change_number))

        info_change = []
        for change in changes:
            line = (change['username'], change['approvals']['Code-Review'])

            if '+1' in line[1] or '+2' in line[1]:
                info_change.append(change['username'])

        have_not_voted = [item for item in info_committers if item not in info_change]
        have_not_voted_length = (len(have_not_voted))

        have_voted = [item for item in info_committers if item in info_change]
        have_voted_length = (len(have_voted))

        log.info("Number of Committers:")
        log.info(len(info_committers))
        committer_lenght = (len(info_committers))

        log.info("Committers that have voted:")
        log.info(have_voted)
        log.info(have_voted_length)
        log.info("Committers that have not voted:")
        log.info(have_not_voted)
        log.info(have_not_voted_length)

        if (have_voted_length == 0):
            log.info("No one has voted:")
            sys.exit(1)

        if (have_voted_length != 0):
            majority = (committer_lenght / have_voted_length)

            if (majority == 1):
                log.info("Majority committer vote reached")
                if (tsc):
                    log.info("Need majority of tsc")
                    info_file = tsc
                    majority_of_committers += 1
                    if majority_of_committers == 2:
                        log.info("TSC majority reached auto merging commit")
                    else:
                        main(ctx, info_file, gerrit_url, change_number, tsc, majority_of_committers)
            else:
                log.info("majority not yet reached")
                sys.exit(1)

    majority_of_committers = 0
    main(ctx, info_file, gerrit_url, change_number, tsc, majority_of_committers)


infofile.add_command(get_committers)
infofile.add_command(sync_committers)
infofile.add_command(check_votes)
