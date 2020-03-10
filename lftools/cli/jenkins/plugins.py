# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Jenkins plugin information."""

__author__ = "Trevor Bramwell"

import click
import requests


def checkmark(truthy):
    """Return a UTF-8 Checkmark or Cross depending on the truthiness of the argument."""
    if truthy:
        return "\u2713"
    return "\u2717"


def print_plugin(plugin, namefield="longName"):
    """Print the plugin longName and version."""
    print("%s:%s" % (plugin[namefield], plugin["version"]))


@click.group()
@click.pass_context
def plugins_init(ctx):
    """Inspect Jenkins plugins on the server."""
    jenkins = ctx.obj["jenkins"]
    ctx.obj["plugins"] = jenkins.server.get_plugins()


@click.command()
@click.pass_context
def list_plugins(ctx):
    """List installed plugins.

    Defaults to listing all installed plugins and their current versions
    """
    plugins = ctx.obj["plugins"]
    for key in plugins.keys():
        _, plugin_name = key
        plugin = plugins[plugin_name]
        print_plugin(plugin)


@click.command()
@click.pass_context
def pinned(ctx):
    """List pinned plugins."""
    plugins = ctx.obj["plugins"]
    for key in plugins.keys():
        _, plugin_name = key
        plugin = plugins[plugin_name]
        if plugin["pinned"]:
            print_plugin(plugin)


@click.command()
@click.pass_context
def dynamic(ctx):
    """List dynamically reloadable plugins."""
    plugins = ctx.obj["plugins"]
    for key in plugins.keys():
        _, plugin_name = key
        plugin = plugins[plugin_name]
        if plugin["supportsDynamicLoad"] == "YES":
            print_plugin(plugin)


@click.command()
@click.pass_context
def needs_update(ctx):
    """List pending plugin updates."""
    plugins = ctx.obj["plugins"]
    for key in plugins.keys():
        _, plugin_name = key
        plugin = plugins[plugin_name]
        if plugin["hasUpdate"]:
            print_plugin(plugin)


@click.command()
@click.pass_context
def enabled(ctx):
    """List enabled plugins."""
    plugins = ctx.obj["plugins"]
    for key in plugins.keys():
        _, plugin_name = key
        plugin = plugins[plugin_name]
        if plugin["enabled"]:
            print_plugin(plugin)


@click.command()
@click.pass_context
def disabled(ctx):
    """List disabled plugins.

    TODO: In the future this should be part of a command alias and pass a flag
    to 'enabled' so that we don't duplicate code.
    """
    plugins = ctx.obj["plugins"]
    for key in plugins.keys():
        _, plugin_name = key
        plugin = plugins[plugin_name]
        if not plugin["enabled"]:
            print_plugin(plugin)


@click.command()
@click.pass_context
def active(ctx):
    """List active plugins."""
    plugins = ctx.obj["plugins"]
    for key in plugins.keys():
        _, plugin_name = key
        plugin = plugins[plugin_name]
        if plugin["active"]:
            print_plugin(plugin)


@click.command()
@click.pass_context
def sec(ctx):
    """List plugins with a known vulnerability.

    Output is in the format:

    Vulnerable Version\t Installed Version\t Link.
    """
    r = requests.get("http://updates.jenkins-ci.org/update-center.actual.json")
    warn = r.json()["warnings"]

    # create a dict of relevant info from jenkins update center
    secdict = {}
    for w in warn:
        name = w["name"]
        url = w["url"]
        for version in w["versions"]:
            lastversion = version.get("lastVersion")
        nv = {name: lastversion}
        secdict.update(nv)

    # create a dict of our active plugins
    activedict = {}
    plugins = ctx.obj["plugins"]
    for key in plugins.keys():
        _, plugin_name = key
        plugin = plugins[plugin_name]
        if plugin["active"]:
            name = plugin["shortName"]
            version = plugin["version"]
            nv = {name: version}
            activedict.update(nv)

    # find the delta
    shared = []
    for key in set(secdict.keys()) & set(activedict.keys()):
        shared.append(key)
        ourversion = activedict[key]
        theirversion = secdict[key]
        t1 = tuple([ourversion])
        t2 = tuple([theirversion])
        if (t1) <= (t2):
            # Print Vulnerable Version\t Installed Version\t Link
            for w in warn:
                name = w["name"]
                url = w["url"]
                for version in w["versions"]:
                    lastversion = version.get("lastVersion")
                if name == key and secdict[key] == lastversion:
                    print("{0}:{1}\t{0}:{2}\t{3}".format(key, secdict[key], activedict[key], url))


plugins_init.add_command(list_plugins, name="list")
plugins_init.add_command(pinned)
plugins_init.add_command(dynamic)
plugins_init.add_command(needs_update, name="needs-update")
plugins_init.add_command(active)
plugins_init.add_command(enabled)
plugins_init.add_command(disabled)
plugins_init.add_command(sec)
