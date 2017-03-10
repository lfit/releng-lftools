# -*- code: utf-8 -*-
# @License EPL-1.0 <http://spdx.org/licenses/EPL-1.0>
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################

__author__ = 'Thanh Ha'


import click

from lftools.openstack import image as os_image


@click.group()
@click.option('--os-cloud', type=str, required=True)
@click.pass_context
def openstack(ctx, os_cloud):
    """Provide an interface to OpenStack."""
    ctx.obj['os_cloud'] = os_cloud
    pass


@openstack.group()
@click.pass_context
def image(ctx):
    """Commands for manipulating images."""
    pass


@click.command()
@click.option('--age-days', type=int, default=0)
@click.pass_context
def cleanup(ctx, age_days):
    """Cleanup old images."""
    os_image.list(ctx.obj['os_cloud'])


@click.command()
@click.option('--age-days', type=int, default=0)
@click.pass_context
def list(ctx, age_days):
    """List cloud images."""
    os_image.cleanup(ctx.obj['os_cloud'], age_days)


image.add_command(cleanup)
image.add_command(list)
