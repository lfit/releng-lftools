# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################

"""Read the Docs interface."""

__author__ = "DW Talton"


import logging
from pprint import pformat

import click

from lftools.api.endpoints import readthedocs

log = logging.getLogger(__name__)


@click.group()
@click.pass_context
def rtd(ctx):
    """Read the Docs interface."""
    pass


@click.command(name="project-list")
@click.pass_context
def project_list(ctx):
    """Get a list of Read the Docs projects.

    Returns a list of RTD projects for the account whose
    token is configured in lftools.ini. This returns the
    slug name, not the pretty name.
    """
    r = readthedocs.ReadTheDocs()
    for project in r.project_list():
        log.info(project)


@click.command(name="project-details")
@click.argument("project-slug")
@click.pass_context
def project_details(ctx, project_slug):
    """Retrieve project details."""
    r = readthedocs.ReadTheDocs()
    data = r.project_details(project_slug)
    log.info(pformat(data))


@click.command(name="project-version-list")
@click.argument("project-slug")
@click.pass_context
def project_version_list(ctx, project_slug):
    """Retrieve project version list."""
    r = readthedocs.ReadTheDocs()
    data = r.project_version_list(project_slug)
    for version in data:
        log.info(version)


@click.command(name="project-version-update")
@click.argument("project-slug")
@click.argument("version-slug")
@click.argument("active", type=click.BOOL)
@click.pass_context
def project_version_update(ctx, project_slug, version_slug, active):
    """Update projects active version.

    active must be one of true or false
    """
    r = readthedocs.ReadTheDocs()
    data = r.project_version_update(project_slug, version_slug, active)
    log.info(data)


@click.command(name="project-version-details")
@click.argument("project-slug")
@click.argument("version-slug")
@click.pass_context
def project_version_details(ctx, project_slug, version_slug):
    """Retrieve project version details."""
    r = readthedocs.ReadTheDocs()
    data = r.project_version_details(project_slug, version_slug)
    log.info(data)


@click.command(name="project-create")
@click.argument("project-name")
@click.argument("repository-url")
@click.argument("repository-type")
@click.argument("homepage")
@click.argument("programming-language")
@click.argument("language")
@click.pass_context
def project_create(ctx, project_name, repository_url, repository_type, homepage, programming_language, language):
    """Create a new project."""
    r = readthedocs.ReadTheDocs()
    data = r.project_create(project_name, repository_url, repository_type, homepage, programming_language, language)
    log.info(pformat(data))


@click.command(
    name="project-update",
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.argument("project-name")
@click.pass_context
def project_update(ctx, project_name):
    """Create a new project."""
    r = readthedocs.ReadTheDocs()
    d = dict()
    for item in ctx.args:
        d.update([item.split("=")])
    data = r.project_update(project_name, d)
    log.info(pformat(data))


@click.command(name="project-build-list")
@click.argument("project-slug")
@click.pass_context
def project_build_list(ctx, project_slug):
    """Retrieve a list of a project's builds."""
    r = readthedocs.ReadTheDocs()
    data = r.project_build_list(project_slug)
    log.info(data)


@click.command(name="project-build-details")
@click.argument("project-slug")
@click.argument("build-id")
@click.pass_context
def project_build_details(ctx, project_slug, build_id):
    """Retrieve specific project build details."""
    r = readthedocs.ReadTheDocs()
    data = r.project_build_details(project_slug, build_id)
    log.info(data)


@click.command(name="project-build-trigger")
@click.argument("project-slug")
@click.argument("version-slug")
@click.pass_context
def project_build_trigger(ctx, project_slug, version_slug):
    """Trigger a new build."""
    r = readthedocs.ReadTheDocs()
    data = r.project_build_trigger(project_slug, version_slug)
    log.info(data)


@click.command(name="subproject-list")
@click.argument("project-slug")
@click.pass_context
def subproject_list(ctx, project_slug):
    """Get a list of Read the Docs subprojects for a project.

    Returns a list of RTD subprojects for a given
    project.
    """
    r = readthedocs.ReadTheDocs()
    for subproject in r.subproject_list(project_slug):
        log.info(subproject)


@click.command(name="subproject-details")
@click.argument("project-slug")
@click.argument("subproject-slug")
@click.pass_context
def subproject_details(ctx, project_slug, subproject_slug):
    """Retrieve subproject's details."""
    r = readthedocs.ReadTheDocs()
    data = r.subproject_details(project_slug, subproject_slug, "expand=active_versions")
    log.info(pformat(data))


@click.command(name="subproject-create")
@click.argument("project-slug")
@click.argument("subproject-slug")
@click.pass_context
def subproject_create(ctx, project_slug, subproject_slug):
    """Create a project-subproject relationship."""
    r = readthedocs.ReadTheDocs()
    data = r.subproject_create(project_slug, subproject_slug)
    log.info(pformat(data))


@click.command(name="subproject-delete")
@click.argument("project-slug")
@click.argument("subproject-slug")
@click.pass_context
def subproject_delete(ctx, project_slug, subproject_slug):
    """Delete a project-subproject relationship."""
    r = readthedocs.ReadTheDocs()
    data = r.subproject_delete(project_slug, subproject_slug)
    if data:
        log.info("Successfully removed the {} {} relationship".format(project_slug, subproject_slug))
    else:
        log.error("Request failed. Is there a subproject relationship?")


rtd.add_command(project_list)
rtd.add_command(project_details)
rtd.add_command(project_version_list)
rtd.add_command(project_version_update)
rtd.add_command(project_version_details)
rtd.add_command(project_create)
rtd.add_command(project_build_list)
rtd.add_command(project_build_details)
rtd.add_command(project_build_trigger)
rtd.add_command(project_update)
rtd.add_command(subproject_list)
rtd.add_command(subproject_details)
rtd.add_command(subproject_create)
rtd.add_command(subproject_delete)
