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


@click.group()
@click.pass_context
def nexus3(ctx):
    """Provide an interface to Nexus3."""
    pass


@nexus3.group()
@click.pass_context
def show(ctx):
    pass


@show.command(name='assets')
@click.argument('fqdn')
@click.argument('repository')
@click.pass_context
def assets(ctx, fqdn, repository):
    r = nexus.Nexus(fqdn=fqdn)
    data = r.list_assets(repository)
    for item in data:
        log.info(pformat(item))


@show.command(name='blobstores')
@click.argument('fqdn')
@click.pass_context
def blobstores(ctx, fqdn):
    r = nexus.Nexus(fqdn=fqdn)
    data = r.list_blobstores()
    log.info(pformat(data))


@show.command(name='components')
@click.argument('fqdn')
@click.argument('repository')
@click.pass_context
def components(ctx, fqdn, repository):
    r = nexus.Nexus(fqdn=fqdn)
    data = r.list_components(repository)
    log.info(pformat(data))


@show.command(name='privileges')
@click.argument('fqdn')
@click.pass_context
def privileges(ctx, fqdn):
    r = nexus.Nexus(fqdn=fqdn)
    data = r.list_privileges()
    log.info(tabulate(data, headers=["Type", "Name", "Description", "Read Only"]))


@show.command(name='repositories')
@click.argument('fqdn')
@click.pass_context
def repositories(ctx, fqdn):
    r = nexus.Nexus(fqdn=fqdn)
    data = r.list_repositories()
    log.info(pformat(data))


@show.command(name='roles')
@click.argument('fqdn')
@click.pass_context
def roles(ctx, fqdn):
    r = nexus.Nexus(fqdn=fqdn)
    data = r.list_roles()
    log.info(tabulate(data, headers=["Roles"]))


@show.command(name='scripts')
@click.argument('fqdn')
@click.pass_context
def scripts(ctx, fqdn):
    r = nexus.Nexus(fqdn=fqdn)
    data = r.list_scripts()
    log.info(pformat(data))


@show.command(name='tasks')
@click.argument('fqdn')
@click.pass_context
def tasks(ctx, fqdn):
    r = nexus.Nexus(fqdn=fqdn)
    data = r.list_tasks()
    log.info(tabulate(data, headers=["Name", "Message", "Current State", "Last Run Result"]))


@show.command(name='user')
@click.argument('fqdn')
@click.argument('username')
@click.pass_context
def user(ctx, fqdn, username):
    r = nexus.Nexus(fqdn=fqdn, username=username)
    data = r.list_user(username)
    log.info(tabulate(data, headers=["User ID", "First Name", "Last Name", "Email Address", "Status", "Roles"]))


@show.command(name='users')
@click.argument('fqdn')
@click.pass_context
def users(ctx, fqdn):
    r = nexus.Nexus(fqdn=fqdn)
    data = r.list_users()
    log.info(tabulate(data, headers=["User ID", "First Name", "Last Name", "Email Address", "Status", "Roles"]))





# @click.command()
# @click.option('-s', '--settings', type=str, required=True)
# @click.pass_context
# def reorder_staged_repos(ctx, settings):
#     """Reorder staging repositories in Nexus.
#
#     Reorders staging repositories in Nexus such that the newest repository gets
#     priority in the aggregate repo.
#     """
#     nexuscmd.reorder_staged_repos(settings)
#
#
# nexus.add_command(reorder_staged_repos)
#
#
# @nexus.group()
# @click.pass_context
# def create(ctx):
#     """Create resources in Nexus."""
#     pass
#
#
# @create.command()
# @click.option(
#     '-c', '--config', type=str, required=True,
#     help='Repo config file for how the Nexus repository should be created.')
# @click.option(
#     '-s', '--settings', type=str, required=True,
#     help='Config file containing administrative settings.')
# @click.pass_context
# def repo(ctx, config, settings):
#     """Create a Nexus repository as defined by a repo-config.yaml file."""
#     nexuscmd.create_repos(config, settings)
#
#
# @create.command()
# @click.option(
#     '-c', '--config', type=str, required=True,
#     help='Role config file for how the Nexus role should be created.')
# @click.option(
#     '-s', '--settings', type=str, required=True,
#     help='Config file containing administrative settings.')
# @click.pass_context
# def role(ctx, config, settings):
#     """Create a Nexus role as defined by a role-config.yaml file."""
#     nexuscmd.create_roles(config, settings)
#
#
# @nexus.group()
# @click.pass_context
# def docker(ctx):
#     """Docker repos in Nexus."""
#     pass
#
#
# def docker_params(command):
#     """Common options and arguments for all docker subcommands."""
#     command = click.option(
#         '--settings', type=str,
#         help=('Yaml file containing "nexus" (url), "user", and "password" '
#               'definitions.'))(command)
#     command = click.option(
#         '-s', '--server', type=str,
#         help=('Nexus server URL. Can also be set as {} in the environment. '
#               'This will override any URL set in settings.yaml.').format(
#                   NEXUS_URL_ENV))(command)
#     command = click.argument('REPO', type=str)(command)
#     command = click.argument('PATTERN', type=str, default="*")(command)
#     return command
#
#
# @docker.command(name="list")
# @docker_params
# @click.option(
#     '--csv', type=click.Path(dir_okay=False, writable=True),
#     help='Write a csv file of the search results to PATH.')
# @click.pass_context
# def list_images(ctx, settings, server, repo, pattern, csv):
#     """List images matching the PATTERN.
#
#     Use '*' for wildcard, or begin with '!' to search for images NOT matching
#     the string.
#     """
#     if not server and NEXUS_URL_ENV in environ:
#         server = environ[NEXUS_URL_ENV]
#     images = nexuscmd.search(settings, server, repo, pattern)
#     if images:
#         nexuscmd.output_images(images, csv)
#
#
# @docker.command(name="delete")
# @docker_params
# @click.option(
#     '-y', '--yes', is_flag=True, help="Answer yes to all prompts")
# @click.pass_context
# def delete_images(ctx, settings, server, repo, pattern, yes):
#     """Delete all images matching the PATTERN.
#
#     By default, prints to console only. Use '*' for wildcard, or begin with '!'
#     to delete images NOT matching the string.
#     """
#     images = nexuscmd.search(settings, server, repo, pattern)
#     if yes or click.confirm("Would you like to delete all {} images?".format(
#             str(len(images)))):
#         nexuscmd.delete_images(settings, server, images)
#
#
# @nexus.command()
# @click.pass_context
# @click.argument('REPOS', type=str, nargs=-1)
# @click.option('-v', '--verify-only', 'verify', is_flag=True, required=False)
# @click.option(
#     '-s', '--server', type=str,
#     help=('Nexus server URL. Can also be set as {} in the environment. '
#           'This will override any URL set in settings.yaml.').format(
#               NEXUS_URL_ENV))
# def release(ctx, repos, verify, server):
#     """Release one or more staging repositories."""
#     if not server and NEXUS_URL_ENV in environ:
#         server = environ[NEXUS_URL_ENV]
#     nexuscmd.release_staging_repos(repos, verify, server)
#
#
# @docker.command(name="releasedockerhub")
# @click.option(
#     '-o', '--org', type=str, required=True,
#     help='Specify repository organization.')
# @click.option(
#     '-r', '--repo', type=str, default='', required=False,
#     help='Only repos containing this string will be selected. '
#          'Default set to blank string, which is every repo.')
# @click.option(
#     '-e', '--exact', is_flag=True, required=False, default=False,
#     help='Match the exact repo name. '
#          'If used, --repo parameter can not be empty.')
# @click.option(
#     '-s', '--summary', is_flag=True, required=False,
#     help='Prints a summary of missing docker tags.')
# @click.option(
#     '-v', '--verbose', is_flag=True, required=False,
#     help='Prints all collected repo/tag information.')
# @click.option(
#     '-c', '--copy', is_flag=True, required=False, default=False,
#     help='Copy missing tags from Nexus3 repos to Docker Hub repos.')
# @click.option(
#     '-p', '--progbar', is_flag=True, required=False, default=False,
#     help='Display a progress bar for the time consuming jobs.')
# @click.pass_context
# def copy_from_nexus3_to_dockerhub(ctx, org, repo, exact, summary, verbose, copy, progbar):
#     """Find missing repos in Docker Hub, Copy from Nexus3.
#
#     Will by default list all missing repos in Docker Hub, compared to Nexus3.
#     If -c (--copy) is provided, it will copy the repos from Nexus3 to Docker Hub.
#     """
#     rdh.start_point(org, repo, exact, summary, verbose, copy, progbar)
