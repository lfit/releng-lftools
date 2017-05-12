# @License EPL-1.0 <http://spdx.org/licenses/EPL-1.0>
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Jenkins Plugin information."""

__author__ = 'Trevor Bramwell'

import click


def checkmark(truthy):
    """Return a UTF-8 Checkmark or Cross depending on the truthiness of the argument."""
    if truthy:
        return u'\u2713'
    return u'\u2717'


@click.group()
@click.pass_context
def plugins(ctx):
    """Inspect Jenkins plugins on the server."""
    ctx.obj['plugins'] = ctx.obj['server'].get_plugins()


@click.command()
@click.pass_context
def list_plugins(ctx):
    """List installed plugins.

    Defaults to listing all installed plugins and their current versions
    """
    plugins = ctx.obj['plugins']
    for key in plugins.keys():
        _, plugin_name = key
        plugin = plugins[plugin_name]
        print("%s [%s] [%s] [%s] [%s]" % (
              plugin_name,
              plugin['version'],
              plugin['enabled'],
              plugin['active'],
              plugin['hasUpdate']))


@click.command()
@click.pass_context
def pinned(ctx):
    """List pinned plugins."""
    plugins = ctx.obj['plugins']
    for key in plugins.keys():
        _, plugin_name = key
        plugin = plugins[plugin_name]
        if plugin['pinned']:
            print("%s" % plugin_name)


@click.command()
@click.pass_context
def dynamic(ctx):
    """List dynamically reloadable plugins."""
    plugins = ctx.obj['plugins']
    for key in plugins.keys():
        _, plugin_name = key
        plugin = plugins[plugin_name]
        if plugin['supportsDynamicLoad'] == "YES":
            print("%s" % plugin_name)


@click.command()
@click.pass_context
def needs_update(ctx):
    """List pending plugin updates."""
    plugins = ctx.obj['plugins']
    for key in plugins.keys():
        _, plugin_name = key
        plugin = plugins[plugin_name]
        if plugin['hasUpdate']:
            print("%s" % plugin_name)


@click.command()
@click.pass_context
def enabled(ctx):
    """List enabled plugins."""
    plugins = ctx.obj['plugins']
    for key in plugins.keys():
        _, plugin_name = key
        plugin = plugins[plugin_name]
        if plugin['enabled']:
            print("%s" % plugin_name)


@click.command()
@click.pass_context
def disabled(ctx):
    """List disabled plugins.

    TODO: In the future this should be part of a command alias and pass a flag
    to 'enabled' so that we don't duplicate code.
    """
    plugins = ctx.obj['plugins']
    for key in plugins.keys():
        _, plugin_name = key
        plugin = plugins[plugin_name]
        if not plugin['enabled']:
            print("%s" % plugin_name)


@click.command()
@click.pass_context
def active(ctx):
    """List active plugins."""
    plugins = ctx.obj['plugins']
    for key in plugins.keys():
        _, plugin_name = key
        plugin = plugins[plugin_name]
        if plugin['active']:
            print("%s" % plugin_name)


plugins.add_command(list_plugins, name='list')
plugins.add_command(pinned)
plugins.add_command(dynamic)
plugins.add_command(needs_update, name='needs-update')
plugins.add_command(active)
plugins.add_command(enabled)
plugins.add_command(disabled)
