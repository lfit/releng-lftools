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

__author__ = "Thanh Ha"


import re
import subprocess

import click

from lftools.openstack import image as os_image
from lftools.openstack import object as os_object
from lftools.openstack import server as os_server
from lftools.openstack import stack as os_stack
from lftools.openstack import volume as os_volume


@click.group()
@click.option("--os-cloud", envvar="OS_CLOUD", type=str, required=True)
@click.pass_context
def openstack(ctx, os_cloud):
    """Provide an interface to OpenStack."""
    ctx.obj["os_cloud"] = os_cloud


@openstack.group()
@click.pass_context
def image(ctx):
    """Command for manipulating images."""
    pass


@click.command()
@click.option(
    "--ci-managed", type=bool, default=False, help="Filter only images that have the ci_managed=yes metadata set."
)
@click.option("--days", type=int, default=0, help="Find images older than or equal to days.")
@click.option("--hide-public", type=bool, default=False, help="Ignore public images.")
@click.option(
    "--clouds",
    type=str,
    default=None,
    help=(
        "Clouds (as defined in clouds.yaml) to remove images from. If not"
        "passed will assume from os-cloud parameter. (optional)"
    ),
)
@click.pass_context
def cleanup(ctx, days, hide_public, ci_managed, clouds):
    """Cleanup old images."""
    os_image.cleanup(ctx.obj["os_cloud"], ci_managed=ci_managed, days=days, hide_public=hide_public, clouds=clouds)


@click.command()
@click.option(
    "--ci-managed", type=bool, default=False, help="Filter only images that have the ci_managed=yes metadata set."
)
@click.option("--days", type=int, default=0, help="Find images older than or equal to days.")
@click.option("--hide-public", type=bool, default=False, help="Ignore public images.")
@click.pass_context
def list(ctx, days, hide_public, ci_managed):
    """List cloud images."""
    os_image.list(ctx.obj["os_cloud"], ci_managed=ci_managed, days=days, hide_public=hide_public)


@click.command()
@click.argument("image")
@click.argument("dest", nargs=-1)
@click.pass_context
def share(ctx, image, dest):
    """Share image with another tenant."""
    os_image.share(ctx.obj["os_cloud"], image, dest)


@click.command()
@click.argument("image")
@click.argument("name", nargs=-1, required=True)
@click.option("--disk-format", type=str, default="raw", help="Disk format of image. (default: raw)")
@click.pass_context
def upload(ctx, image, name, disk_format):
    """Upload image to OpenStack cloud."""
    name = " ".join(name)

    disktype = subprocess.check_output(["qemu-img", "info", image]).decode("utf-8")
    pattern = disk_format
    result = re.search(pattern, disktype)
    if result:
        print("PASS Image format matches {}".format(disk_format))
    else:
        print("ERROR Image is not in {} format".format(disk_format))
        exit(1)

    os_image.upload(ctx.obj["os_cloud"], image, name, disk_format)


image.add_command(cleanup)
image.add_command(list)
image.add_command(share)
image.add_command(upload)


@openstack.group()
@click.pass_context
def object(ctx):
    """Command for manipulating objects."""
    pass


@click.command()
@click.pass_context
def list_containers(ctx):
    """List available containers."""
    os_object.list_containers(ctx.obj["os_cloud"])


object.add_command(list_containers)


@openstack.group()
@click.pass_context
def server(ctx):
    """Command for manipulating servers."""
    pass


@click.command()
@click.option("--days", type=int, default=0, help="Find servers older than or equal to days.")
@click.pass_context
def cleanup(ctx, days):
    """Cleanup old servers."""
    os_server.cleanup(ctx.obj["os_cloud"], days=days)


@click.command()
@click.option("--days", type=int, default=0, help="Find servers older than or equal to days.")
@click.pass_context
def list(ctx, days):
    """List cloud servers."""
    os_server.list(ctx.obj["os_cloud"], days=days)


@click.command()
@click.argument("server")
@click.option("--minutes", type=int, default=0, help="Delete server if older than x minutes.")
@click.pass_context
def remove(ctx, server, minutes):
    """Remove servers."""
    os_server.remove(ctx.obj["os_cloud"], server_name=server, minutes=minutes)


server.add_command(cleanup)
server.add_command(list)
server.add_command(remove)


@openstack.group()
@click.pass_context
def stack(ctx):
    """Command for manipulating stacks."""
    pass


@click.command()
@click.argument("name")
@click.argument("template_file")
@click.argument("parameter_file")
@click.option("--timeout", type=int, default=900, help="Stack create timeout in seconds.")
@click.option("--tries", type=int, default=2, help="Number of tries before giving up.")
@click.pass_context
def create(ctx, name, template_file, parameter_file, timeout, tries):
    """Create stack."""
    os_stack.create(ctx.obj["os_cloud"], name, template_file, parameter_file, timeout, tries)


@click.command()
@click.argument("name_or_id")
@click.option("--force", type=bool, is_flag=True, default=False, help="Ignore timeout and continue with next stack.")
@click.option("--timeout", type=int, default=900, help="Stack delete timeout in seconds.")
@click.pass_context
def delete(ctx, name_or_id, force, timeout):
    """Delete stack."""
    os_stack.delete(ctx.obj["os_cloud"], name_or_id, force=force, timeout=timeout)


@click.command()
@click.argument("stack_name")
@click.pass_context
def cost(ctx, stack_name):
    """Get Total Stack Cost."""
    os_stack.cost(ctx.obj["os_cloud"], stack_name)


@click.command(name="delete-stale")
@click.argument("jenkins_urls", nargs=-1)
@click.pass_context
def delete_stale(ctx, jenkins_urls):
    """Delete stale stacks.

    This command checks Jenkins and OpenStack for stacks that do not appear in
    both places. If a stack is no longer available in Jenkins but is in
    OpenStack then it is considered stale. Stale stacks are then deleted.
    """
    os_stack.delete_stale(ctx.obj["os_cloud"], jenkins_urls)


stack.add_command(create)
stack.add_command(delete)
stack.add_command(delete_stale)
stack.add_command(cost)


@openstack.group()
@click.pass_context
def volume(ctx):
    """Command for manipulating volumes."""
    pass


@click.command()
@click.option("--days", type=int, default=0, help="Find volumes older than or equal to days.")
@click.pass_context
def cleanup(ctx, days):
    """Cleanup old volumes."""
    os_volume.cleanup(ctx.obj["os_cloud"], days=days)


@click.command()
@click.option("--days", type=int, default=0, help="Find volumes older than or equal to days.")
@click.pass_context
def list(ctx, days):
    """List cloud volumes."""
    os_volume.list(ctx.obj["os_cloud"], days=days)


@click.command()
@click.argument("volume_id")
@click.option("--minutes", type=int, default=0, help="Delete volumes if older than x minutes.")
@click.pass_context
def remove(ctx, volume_id, minutes):
    """Remove volumes."""
    os_volume.remove(ctx.obj["os_cloud"], volume_id=volume_id, minutes=minutes)


volume.add_command(cleanup)
volume.add_command(list)
volume.add_command(remove)
