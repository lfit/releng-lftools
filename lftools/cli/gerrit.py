#!/usr/bin/env python3
# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2018 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Create a gerrit project."""

from __future__ import print_function

import click

import logging
from pprint import pformat


from lftools.api.endpoints import gerrit
from lftools.gerrit_helper import helper_addinfofile
from lftools.gerrit_helper import helper_addinfojob
from lftools.gerrit_helper import helper_createproject
from lftools.gerrit_helper import helper_prepareproject

log = logging.getLogger(__name__)

@click.group()
@click.pass_context
def gerrit_cli(ctx):
    """GERRIT TOOLS."""
    pass


@click.command(name='addinfofile')
@click.argument('gerrit_fqdn')
@click.argument('gerrit_project')
@click.argument('info_file')
@click.pass_context
def addinfofile(ctx, gerrit_fqdn, gerrit_project, info_file):
    """Add an INFO file for review to a Project.

    Requires gerrit directory.

    Example:

    gerrit_url gerrit.o-ran-sc.org/r
    gerrit_project test/test1
    """
    g = gerrit.Gerrit(fqdn=gerrit_fqdn)
    data = g.add_info_file(gerrit_fqdn, gerrit_project, info_file)
    log.info(pformat(data))


@click.command(name='addinfojob')
@click.argument('gerrit_url')
@click.argument('gerrit_project')
@click.argument('jjbrepo')
@click.option('--reviewid', type=str, required=False,
              help='ammend a review rather than making a new one')
@click.pass_context
def addinfojob(ctx, gerrit_url, gerrit_project, jjbrepo, reviewid):
    """Add an INFO job for a new Project.

    Adds info verify jenkins job for project.
    result['id'] can be used to ammend a review
    so that multiple projects can have info jobs added
    in a single review

    Example:

    gerrit_url gerrit.o-ran-sc.org/r
    gerrit_project test/test1
    jjbrepo ci-mangement
    """
    helper_addinfojob(ctx, gerrit_url, gerrit_project, jjbrepo, reviewid)


@click.command(name='prepareproject')
@click.argument('gerrit_url')
@click.argument('gerrit_project')
@click.argument('info_file')
@click.pass_context
def prepareproject(ctx, gerrit_url, gerrit_project, info_file):
    """Prepare a newly created project.

    Newly created project is given a .gitreview.
    Github group is given read
    INFO.yaml is submitted for review.

    Example:

    gerrit_url gerrit.o-ran-sc.org/r
    gerrit_project test/test1
    TODO: prolog rule that dissalows self submit
    """
    helper_prepareproject(ctx, gerrit_url, gerrit_project, info_file)


# Creates a gerrit project if project does not exist and adds ldap group as owner.
# TODO: does not support inherited permissions from other than All-Projects.
@click.command(name='createproject')
@click.argument('gerrit_url')
@click.argument('gerrit_project')
@click.argument('ldap_group')
@click.option('--check', is_flag=True,
              help='just check if the project exists')
@click.pass_context
def createproject(ctx, gerrit_url, gerrit_project, ldap_group, check):
    """Create a project via the gerrit API.

    Creates a gerrit project.
    Sets ldap group as owner.

    Example:

    gerrit_url gerrit.o-ran-sc.org/r
    gerrit_project test/test1
    ldap_group oran-gerrit-test-test1-committers

    """
    helper_createproject(ctx, gerrit_url, gerrit_project, ldap_group, check)


gerrit_cli.add_command(addinfojob)
gerrit_cli.add_command(addinfofile)
gerrit_cli.add_command(prepareproject)
gerrit_cli.add_command(createproject)
