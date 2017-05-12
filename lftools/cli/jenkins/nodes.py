# @License EPL-1.0 <http://spdx.org/licenses/EPL-1.0>
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Jenkins information"""

__author__ = 'Trevor Bramwell'

import click


def offline_str(status):
    """Convert the offline node status from a boolean to a string"""
    if status:
        return "Offline"
    return "Online"


@click.group()
@click.pass_context
def nodes(ctx):
    """Find information about builders connected to Jenkins Master."""
    ctx.obj['nodes'] = ctx.obj['server'].get_nodes()


@click.command()
@click.pass_context
def list_nodes(ctx):
    """List Jenkins nodes."""
    nodes = ctx.obj['nodes']

    for node in nodes:
        print("%s [%s]" % (node['name'], offline_str(node['offline'])))


nodes.add_command(list_nodes, name='list')
