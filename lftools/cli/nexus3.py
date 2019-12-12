# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""CLI entry point for nexus3 commands."""

import logging

from pprint import pformat
from tabulate import tabulate

import click

from lftools.api.endpoints import nexus

log = logging.getLogger(__name__)


# <editor-fold desc="Primary command groups">
@click.group()
@click.argument('fqdn')
@click.pass_context
def nexus3(ctx, fqdn):
    """Provide an interface to Nexus3."""
    nexus_obj = nexus.Nexus(fqdn=fqdn)
    ctx.obj = {
        'nexus': nexus_obj
    }
    pass


@nexus3.group()
@click.pass_context
def asset(ctx):
    pass


@nexus3.group()
@click.pass_context
def misc(ctx):
    pass


@nexus3.group()
@click.pass_context
def privilege(ctx):
    pass


@nexus3.group()
@click.pass_context
def repository(ctx):
    pass


@nexus3.group()
@click.pass_context
def role(ctx):
    pass


@nexus3.group()
@click.pass_context
def script(ctx):
    pass


@nexus3.group()
@click.pass_context
def task(ctx):
    pass


@nexus3.group()
@click.pass_context
def user(ctx):
    pass
# </editor-fold>


# <editor-fold desc="asset subcommands">
# asset subcommands
@asset.command(name='list')
@click.argument('repository')
@click.pass_context
def asset_list(ctx, repository):
    r = ctx.obj['nexus']
    data = r.list_assets(repository)
    for item in data:
        log.info(pformat(item))


@asset.command(name='search')
@click.argument('query-string')
@click.argument('repository')
@click.option('--details', is_flag=True)
@click.pass_context
def asset_search(ctx, query_string, repository, details):
    r = ctx.obj['nexus']
    data = r.search_asset(query_string, repository, details)

    if details:
        log.info(data)
    else:
        for item in data:
            log.info(item)

# </editor-fold>


# <editor-fold desc="misc subcommands">
# misc subcommands
@misc.command(name='list-blobstores')
@click.pass_context
def list_blobstores(ctx):
    r = ctx.obj['nexus']
    data = r.list_blobstores()
    log.info(pformat(data))


@misc.command(name='list-components')
@click.argument('repository')
@click.pass_context
def list_components(ctx, repository):
    r = ctx.obj['nexus']
    data = r.list_components(repository)
    log.info(pformat(data))
# </editor-fold>


# <editor-fold desc="privilege subcommands">
# privilege subcommands
@privilege.command(name='list')
@click.pass_context
def list_privileges(ctx):
    r = ctx.obj['nexus']
    data = r.list_privileges()
    log.info(tabulate(data, headers=["Type", "Name", "Description", "Read Only"]))
# </editor-fold>


# <editor-fold desc="repository subcommands">
# repository subcommands
@repository.command(name='list')
@click.pass_context
def list_repositories(ctx):
    r = ctx.obj['nexus']
    data = r.list_repositories()
    log.info(pformat(data))
# </editor-fold>


# <editor-fold desc="role subcommands">
# role subcommands
@role.command(name='list')
@click.pass_context
def list_roles(ctx, fqdn):
    r = ctx.obj['nexus']
    data = r.list_roles()
    log.info(tabulate(data, headers=["Roles"]))


@role.command(name='create')
@click.argument('name')
@click.argument('description')
@click.argument('privileges')
@click.argument('roles')
@click.pass_context
def create_role(ctx, name, description, privileges, roles):
    r = ctx.obj['nexus']
    data = r.create_role(name, description, privileges, roles)
    log.info(pformat(data))
# </editor-fold>


# <editor-fold desc="script subcommands">
# script subcommands
@script.command(name='list')
@click.pass_context
def list_scripts(ctx):
    r = ctx.obj['nexus']
    data = r.list_scripts()
    log.info(pformat(data))


@script.command(name='create')
@click.argument('name')
@click.argument('filename')
@click.pass_context
def create_script(ctx, name, filename):
    r = ctx.obj['nexus']
    data = r.create_script(name, filename)
    log.info(pformat(data))
# </editor-fold>


# status subcommands


# <editor-fold desc="task subcommands">
# task subcommands
@task.command(name='list')
@click.pass_context
def list_tasks(ctx):
    r = ctx.obj['nexus']
    data = r.list_tasks()
    log.info(tabulate(data, headers=["Name", "Message", "Current State", "Last Run Result"]))
# </editor-fold>


# <editor-fold desc="user subcommands">
# user subcommands
@user.command(name='search')
@click.argument('username')
@click.pass_context
def search_user(ctx, username):
    r = ctx.obj['nexus']
    data = r.list_user(username)
    log.info(tabulate(data, headers=["User ID", "First Name", "Last Name", "Email Address", "Status", "Roles"]))
# </editor-fold>

