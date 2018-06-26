#!/usr/bin/env python2
# SPDX-License-Identifier: Apache-2.0
##############################################################################
# Copyright (c) 2018 The Linux Foundation and others.
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import yaml
import click

@click.command()
@click.option('--file', envvar='', type=str, required=True)
@click.option('--full', envvar='', type=str, required=False)
@click.option('--single', envvar='', type=str, required=False)
@click.pass_context
def parseinfofile(ctx, file, full, single):
    """
    List committers from INFO.yaml
    """
    with open(file, 'r') as yaml_file:
        project = yaml.safe_load(yaml_file)

    def list_committers(full, single, project):
        """List commiters from the INFO.yaml file"""
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
