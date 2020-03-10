# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Jenkins build information."""

__author__ = "Trevor Bramwell"

import click


@click.group()
@click.pass_context
def builds(ctx):
    """Information regarding current builds and the queue."""
    pass


@click.command()
@click.pass_context
def running(ctx):
    """Show all the currently running builds."""
    jenkins = ctx.obj["jenkins"]
    running_builds = jenkins.server.get_running_builds()

    for build in running_builds:
        print("- %s on %s" % (build["name"], build["node"]))


@click.command()
@click.pass_context
def queued(ctx):
    """Show all jobs waiting in the queue and their status."""
    jenkins = ctx.obj["jenkins"]
    queue = jenkins.server.get_queue_info()

    queue_length = len(queue)
    print("Build Queue (%s)" % queue_length)
    for build in queue:
        print(" - %s" % (build["task"]["name"])),
        if build["stuck"]:
            print("[Stuck]")
        if build["blocked"]:
            print("[Blocked]")


builds.add_command(running)
builds.add_command(queued)
