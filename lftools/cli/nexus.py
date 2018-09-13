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
import click

from lftools.nexus import cmd as nexuscmd


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
        '-s', '--settings', type=str,
        help='Yaml file containing "nexus" (url), "user", and "password" '
        + 'definitions.')(command)
    command = click.option(
        '-u', '--url', type=str,
        help='Override "nexus" setting in settings.yaml file (alternatively, '
        + 'this can be used when credentials are defined in '
        + 'lftools.ini)')(command)
    command = click.argument('REPO', type=str)(command)
    command = click.argument('PATTERN', type=str, default="*")(command)
    return command


@docker.command(name="list")
@docker_params
@click.option(
    '--csv', type=click.Path(dir_okay=False, writable=True),
    help='Write a csv file of the search results to PATH.')
@click.pass_context
def list_images(ctx, settings, url, repo, pattern, csv):
    """List images matching the PATTERN.

    Use '*' for wildcard, or begin with '!' to search for images NOT matching
    the string.
    """
    images = nexuscmd.search(settings, url, repo, pattern)
    nexuscmd.output_images(images, csv)


@docker.command(name="delete")
@docker_params
@click.option(
    '-y', '--yes', is_flag=True, help="Answer yes to all prompts")
@click.pass_context
def delete_images(ctx, settings, url, repo, pattern, yes):
    """Delete all images matching the PATTERN.

    Use '*' for wildcard, or begin with '!' to delete images NOT matching the
    string.
    """
    images = nexuscmd.search(settings, url, repo, pattern)
    if yes or click.confirm("Would you like to delete all " + str(len(images))
                            + " images?"):
        nexuscmd.delete_images(settings, url, images, yes)
