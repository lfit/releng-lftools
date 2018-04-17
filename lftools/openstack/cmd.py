# -*- code: utf-8 -*-
# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""CLI configuration for openstack command."""

__author__ = 'Thanh Ha'


import click

from lftools.openstack import image as os_image
from lftools.openstack import server as os_server
from lftools.openstack import volume as os_volume


@click.group()
@click.option('--os-cloud', envvar='OS_CLOUD', type=str, required=True)
@click.pass_context
def openstack(ctx, os_cloud):
    """Provide an interface to OpenStack."""
    ctx.obj['os_cloud'] = os_cloud


@openstack.group()
@click.pass_context
def image(ctx):
    """Command for manipulating images."""
    pass


@click.command()
@click.option(
    '--ci-managed', type=bool, default=True,
    help='Filter only images that have the ci_managed=yes metadata set.')
@click.option(
    '--days', type=int, default=0,
    help='Find images older than or equal to days.')
@click.option(
    '--hide-public', type=bool, default=False,
    help='Ignore public images.')
@click.option(
    '--clouds', type=str, default=None,
    help=('Clouds (as defined in clouds.yaml) to remove images from. If not'
          'passed will assume from os-cloud parameter. (optional)'))
@click.pass_context
def cleanup(ctx, days, hide_public, ci_managed, clouds):
    """Cleanup old images."""
    os_image.cleanup(
        ctx.obj['os_cloud'],
        ci_managed=ci_managed,
        days=days,
        hide_public=hide_public,
        clouds=clouds)


@click.command()
@click.option(
    '--ci-managed', type=bool, default=True,
    help='Filter only images that have the ci_managed=yes metadata set.')
@click.option(
    '--days', type=int, default=0,
    help='Find images older than or equal to days.')
@click.option(
    '--hide-public', type=bool, default=False,
    help='Ignore public images.')
@click.pass_context
def list(ctx, days, hide_public, ci_managed):
    """List cloud images."""
    os_image.list(
        ctx.obj['os_cloud'],
        ci_managed=ci_managed,
        days=days,
        hide_public=hide_public)


image.add_command(cleanup)
image.add_command(list)


@openstack.group()
@click.pass_context
def server(ctx):
    """Command for manipulating servers."""
    pass


@click.command()
@click.option(
    '--days', type=int, default=0,
    help='Find servers older than or equal to days.')
@click.pass_context
def cleanup(ctx, days):
    """Cleanup old servers."""
    os_server.cleanup(
        ctx.obj['os_cloud'],
        days=days)


@click.command()
@click.option(
    '--days', type=int, default=0,
    help='Find servers older than or equal to days.')
@click.pass_context
def list(ctx, days):
    """List cloud servers."""
    os_server.list(
        ctx.obj['os_cloud'],
        days=days)


@click.command()
@click.argument('server')
@click.option(
    '--minutes', type=int, default=0,
    help='Delete server if older than x minutes.')
@click.pass_context
def remove(ctx, server, minutes):
    """Remove servers."""
    os_server.remove(
        ctx.obj['os_cloud'],
        server_name=server,
        minutes=minutes)


server.add_command(cleanup)
server.add_command(list)
server.add_command(remove)


@openstack.group()
@click.pass_context
def volume(ctx):
    """Command for manipulating volumes."""
    pass


@click.command()
@click.option(
    '--days', type=int, default=0,
    help='Find volumes older than or equal to days.')
@click.pass_context
def cleanup(ctx, days):
    """Cleanup old volumes."""
    os_volume.cleanup(
        ctx.obj['os_cloud'],
        days=days)


@click.command()
@click.option(
    '--days', type=int, default=0,
    help='Find volumes older than or equal to days.')
@click.pass_context
def list(ctx, days):
    """List cloud volumes."""
    os_volume.list(
        ctx.obj['os_cloud'],
        days=days)


@click.command()
@click.argument('volume')
@click.option(
    '--minutes', type=int, default=0,
    help='Delete volumes if older than x minutes.')
@click.pass_context
def remove(ctx, volume, minutes):
    """Remove volumes."""
    os_volume.remove(
        ctx.obj['os_cloud'],
        volume_name=volume,
        minutes=minutes)


volume.add_command(cleanup)
volume.add_command(list)
volume.add_command(remove)
