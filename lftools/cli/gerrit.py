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

import logging
from pprint import pformat

import click

from lftools.api.endpoints import gerrit

log = logging.getLogger(__name__)


@click.group()
@click.pass_context
def gerrit_cli(ctx):
    """GERRIT TOOLS."""
    pass


@click.command(name="addfile")
@click.argument("gerrit_fqdn")
@click.argument("gerrit_project")
@click.argument("filename")
@click.option("--issue_id", type=str, required=False, help="For projects that enforce an issue id for changesets")
@click.option("--file_location", type=str, required=False, help="option allos you to specify full path and file name")
@click.pass_context
def addfile(ctx, gerrit_fqdn, gerrit_project, filename, issue_id, file_location):
    """Add an file for review to a Project.

    Requires gerrit directory.

    Example:

    gerrit_url gerrit.o-ran-sc.org/r
    gerrit_project test/test1
    """
    g = gerrit.Gerrit(fqdn=gerrit_fqdn)
    data = g.add_file(gerrit_fqdn, gerrit_project, filename, issue_id, file_location)
    log.info(pformat(data))


@click.command(name="addinfojob")
@click.argument("gerrit_fqdn")
@click.argument("gerrit_project")
@click.argument("jjbrepo")
@click.option("--reviewid", type=str, required=False, help="ammend a review rather than making a new one")
@click.option("--issue_id", type=str, required=False, help="For projects that enforce an issue id for changesets")
@click.pass_context
def addinfojob(ctx, gerrit_fqdn, gerrit_project, jjbrepo, reviewid, issue_id):
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
    g = gerrit.Gerrit(fqdn=gerrit_fqdn)
    data = g.add_info_job(gerrit_fqdn, gerrit_project, jjbrepo, reviewid, issue_id)
    log.info(pformat(data))


@click.command(name="addgitreview")
@click.argument("gerrit_fqdn")
@click.argument("gerrit_project")
@click.option("--issue_id", type=str, required=False, help="For projects that enforce an issue id for changesets")
@click.pass_context
def addgitreview(ctx, gerrit_fqdn, gerrit_project, issue_id):
    """Add git review to a project.

    Example:
    gerrit_url gerrit.o-ran-sc.org
    gerrit_project test/test1
    """
    g = gerrit.Gerrit(fqdn=gerrit_fqdn)
    data = g.add_git_review(gerrit_fqdn, gerrit_project, issue_id)
    log.info(pformat(data))


@click.command(name="addgithubrights")
@click.argument("gerrit_fqdn")
@click.argument("gerrit_project")
@click.pass_context
def addgithubrights(ctx, gerrit_fqdn, gerrit_project):
    """Grant Github read for a project.

    gerrit_url gerrit.o-ran-sc.org
    gerrit_project test/test1
    """
    g = gerrit.Gerrit(fqdn=gerrit_fqdn)
    data = g.add_github_rights(gerrit_fqdn, gerrit_project)
    log.info(pformat(data))


@click.command(name="abandonchanges")
@click.argument("gerrit_fqdn")
@click.argument("gerrit_project")
@click.pass_context
def abandonchanges(ctx, gerrit_fqdn, gerrit_project):
    """Abandon all OPEN changes for a gerrit project.

    gerrit_url gerrit.o-ran-sc.org
    gerrit_project test/test1
    """
    g = gerrit.Gerrit(fqdn=gerrit_fqdn)
    data = g.abandon_changes(gerrit_fqdn, gerrit_project)
    log.info(pformat(data))


# Creates a gerrit project if project does not exist and adds ldap group as owner.
# Limits: does not support inherited permissions from other than All-Projects.
@click.command(name="createproject")
@click.argument("gerrit_fqdn")
@click.argument("gerrit_project")
@click.argument("ldap_group")
@click.option("--description", type=str, required=True, help="Project Description")
@click.option("--check", is_flag=True, help="just check if the project exists")
@click.pass_context
def createproject(ctx, gerrit_fqdn, gerrit_project, ldap_group, description, check):
    """Create a project via the gerrit API.

    Creates a gerrit project.
    Sets ldap group as owner.

    Example:

    gerrit_url gerrit.o-ran-sc.org/r
    gerrit_project test/test1
    ldap_group oran-gerrit-test-test1-committers

    """
    g = gerrit.Gerrit(fqdn=gerrit_fqdn)
    data = g.create_project(gerrit_fqdn, gerrit_project, ldap_group, description, check)
    log.info(pformat(data))


@click.command(name="create-saml-group")
@click.argument("gerrit_fqdn")
@click.argument("ldap_group")
@click.pass_context
def create_saml_group(ctx, gerrit_fqdn, ldap_group):
    """Create saml group based on ldap group."""
    g = gerrit.Gerrit(fqdn=gerrit_fqdn)
    data = g.create_saml_group(gerrit_fqdn, ldap_group)
    log.info(pformat(data))


@click.command(name="list-project-permissions")
@click.argument("gerrit_fqdn")
@click.argument("project")
@click.pass_context
def list_project_permissions(ctx, gerrit_fqdn, project):
    """List Owners of a Project."""
    g = gerrit.Gerrit(fqdn=gerrit_fqdn)
    data = g.list_project_permissions(project)
    for ldap_group in data:
        log.info(pformat(ldap_group))


@click.command(name="list-project-inherits-from")
@click.argument("gerrit_fqdn")
@click.argument("gerrit_project")
@click.pass_context
def list_project_inherits_from(ctx, gerrit_fqdn, gerrit_project):
    """List who a project inherits from."""
    g = gerrit.Gerrit(fqdn=gerrit_fqdn)
    data = g.list_project_inherits_from(gerrit_project)
    log.info(data)


gerrit_cli.add_command(addinfojob)
gerrit_cli.add_command(addfile)
gerrit_cli.add_command(addgitreview)
gerrit_cli.add_command(addgithubrights)
gerrit_cli.add_command(createproject)
gerrit_cli.add_command(abandonchanges)
gerrit_cli.add_command(create_saml_group)
gerrit_cli.add_command(list_project_permissions)
gerrit_cli.add_command(list_project_inherits_from)
