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
"""Script to extract committer information from an INFO.yaml file."""

import click
import yaml


@click.command()
@click.option('--file', envvar='', type=str, required=True,
              help='File to extract from')
@click.option('--full', envvar='', type=str, required=False,
              help='Output name email and id ')
@click.option('--single', envvar='', type=str, required=False,
              help='Output for a specific lifd')
@click.pass_context
def parseinfofile(ctx, file, full, single):
    """Extract Committer info from INFO.yaml or LDAP dump."""
    with open(file, 'r') as yaml_file:
        project = yaml.safe_load(yaml_file)

    def list_committers(full, single, project):
        """List commiters from the INFO.yaml file."""
        lookup = project.get('committers', [])
        if 'committers' not in project:
            exit(0)

        for item in lookup:
            if full:
                print("    - name: '%s'" % item['name'])
                print("      email: '%s'" % item['email'])
                print("      id: '%s'" % item['id'])
            elif single and item['id'] == (single):
                print("    - name: '%s'" % item['name'])
                print("      email: '%s'" % item['email'])
                print("      id: '%s'" % item['id'])
            elif not full and not single:
                print("      id: '%s'" % item['id'])

    list_committers(full, single, project)
