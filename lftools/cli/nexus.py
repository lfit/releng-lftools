# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""CLI entry point for nexus commands."""
from os import environ

import click

from lftools.nexus import cmd as nexuscmd
import lftools.onap_nexus_2_docker as on2d

NEXUS_URL_ENV = 'NEXUS_URL'


@click.group()
@click.pass_context
def nexus(ctx):
    """Provide an interface to Nexus."""
    pass


@click.command()
@click.option('-s', '--settings', type=str, required=True)
@click.pass_context
def reorder_staged_repos(ctx, settings):
    """Reorder staging repositories in Nexus.

    Reorders staging repositories in Nexus such that the newest repository gets
    priority in the aggregate repo.
    """
    nexuscmd.reorder_staged_repos(settings)


nexus.add_command(reorder_staged_repos)


@nexus.group()
@click.pass_context
def create(ctx):
    """Create resources in Nexus."""
    pass


@create.command()
@click.option(
    '-c', '--config', type=str, required=True,
    help='Repo config file for how to the Nexus repository should be created.')
@click.option(
    '-s', '--settings', type=str, required=True,
    help='Config file containing administrative settings.')
@click.pass_context
def repo(ctx, config, settings):
    """Create a Nexus repository as defined by a repo-config.yaml file."""
    nexuscmd.create_repos(config, settings)


@nexus.group()
@click.pass_context
def docker(ctx):
    """Docker repos in Nexus."""
    pass


def docker_params(command):
    """Common options and arguments for all docker subcommands."""
    command = click.option(
        '--settings', type=str,
        help=('Yaml file containing "nexus" (url), "user", and "password" '
              'definitions.'))(command)
    command = click.option(
        '-s', '--server', type=str,
        help=('Nexus server URL. Can also be set as {} in the environment. '
              'This will override any URL set in settings.yaml.').format(
                  NEXUS_URL_ENV))(command)
    command = click.argument('REPO', type=str)(command)
    command = click.argument('PATTERN', type=str, default="*")(command)
    return command


@docker.command(name="list")
@docker_params
@click.option(
    '--csv', type=click.Path(dir_okay=False, writable=True),
    help='Write a csv file of the search results to PATH.')
@click.pass_context
def list_images(ctx, settings, server, repo, pattern, csv):
    """List images matching the PATTERN.

    Use '*' for wildcard, or begin with '!' to search for images NOT matching
    the string.
    """
    if not server and 'NEXUS_URL_ENV' in environ:
        server = environ['NEXUS_URL_ENV']
    images = nexuscmd.search(settings, server, repo, pattern)
    nexuscmd.output_images(images, csv)


@docker.command(name="delete")
@docker_params
@click.option(
    '-y', '--yes', is_flag=True, help="Answer yes to all prompts")
@click.pass_context
def delete_images(ctx, settings, server, repo, pattern, yes):
    """Delete all images matching the PATTERN.

    By default, prints to console only. Use '*' for wildcard, or begin with '!'
    to delete images NOT matching the string.
    """
    images = nexuscmd.search(settings, server, repo, pattern)
    if yes or click.confirm("Would you like to delete all {} images?".format(
            str(len(images)))):
        nexuscmd.delete_images(settings, server, images)


@docker.command(name="nexus2docker")
@click.option(
    '-o', '--org', type=str, default='onap', required=False,
    help='Specify repository organisation. Default "onap".')
@click.option(
    '-r', '--repo', type=str, default='', required=False,
    help='Only repos containing this string will be selected. '
         'Default set to blank string, which is every repo')
@click.option(
    '-s', '--summary', is_flag=True, default=True, required=False,
    help='Prints a summary of missing docker tags.')
@click.option(
    '-v', '--verbose', is_flag=True, required=False,
    help='Prints all collected repo/tag information.')
@click.option(
    '-c', '--copy', is_flag=True, required=False,
    help='Copy missing tags from Nexus repos to Docker repos.')
@click.pass_context
def copy_from_nexus_to_docker(ctx, org, repo, summary, verbose, copy):
    """Find missing repos in Docker, Copy from Nexus.

    Will by default list all missing repos in docker, compared to Nexus.
    If -c (--copy) is provided, it will copy the repos from Nexus to Docker.
    """
    on2d.start_point(org, repo, summary, verbose, copy)
