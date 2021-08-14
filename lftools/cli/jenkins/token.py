# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2018 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Jenkins token commands."""

__author__ = "Thanh Ha"

import logging
import os
import sys

import click
import requests
from six.moves import configparser

from lftools import config as lftools_cfg
from lftools.jenkins.token import get_token

log = logging.getLogger(__name__)


@click.group()
@click.pass_context
def token(ctx):
    """Get API token."""


@click.command()
@click.option("--name", type=str, default="token-created-by-lftools", help="set token name")
@click.pass_context
def change(ctx, name):
    """Generate a new API token."""
    jenkins = ctx.obj["jenkins"]
    username = ctx.obj["username"]
    password = ctx.obj["password"]

    if not username or not password:
        log.error("Username or password not set.")
        sys.exit(1)

    log.info(get_token(name, jenkins.url, change=True, username=username, password=password))


@click.command()
@click.argument("name")
@click.argument("url")
@click.pass_context
def init(ctx, name, url):
    """Initialize jenkins_jobs.ini config for new server section."""
    jenkins = ctx.obj["jenkins"]
    username = ctx.obj["username"]
    password = ctx.obj["password"]

    if not username or not password:
        log.error("Username or password not set.")
        sys.exit(1)

    _require_jjb_ini(jenkins.config_file)

    config = configparser.ConfigParser()
    config.read(jenkins.config_file)

    token = get_token(url, change=True, username=username, password=password)
    try:
        config.add_section(name)
    except configparser.DuplicateSectionError as e:
        log.error(e)
        sys.exit(1)

    config.set(name, "url", url)
    config.set(name, "user", lftools_cfg.get_setting("global", "username"))
    config.set(name, "password", token)

    with open(jenkins.config_file, "w") as configfile:
        config.write(configfile)


@click.command(name="print")
@click.pass_context
def print_token(ctx):
    """Print current API token."""
    jenkins = ctx.obj["jenkins"]
    username = ctx.obj["username"]
    password = ctx.obj["password"]

    if not username or not password:
        log.error("Username or password not set.")
        sys.exit(1)

    log.info(get_token(jenkins.url, username=username, password=password))


@click.command()
@click.argument("servers", nargs=-1, required=False)
@click.pass_context
def reset(ctx, servers):
    """Regenerate API tokens for configurations in jenkins_jobs.ini.

    This command has 2 modes to reset API tokens:

    1. Single-server: Resets the API token and returns the new token value.
    2. Multi-server: Resets the API token for a provided list of servers and
       returns a summary of the outcome.

    If the server parameter is NOT passed then all servers listed in the
    configuration file will be reset via multi-server mode.
    """
    jenkins = ctx.obj["jenkins"]
    username = ctx.obj["username"]
    password = ctx.obj["password"]

    if not username or not password:
        log.error("Username or password not set.")
        sys.exit(1)

    _require_jjb_ini(jenkins.config_file)

    def _reset_key(config, server):
        url = config.get(server, "url")

        try:
            token = get_token(url, change=True, username=username, password=password)
            config.set(server, "password", token)
            with open(jenkins.config_file, "w") as configfile:
                config.write(configfile)
            return token
        except requests.exceptions.ConnectionError:
            return None

    fail = 0
    success = 0
    config = configparser.ConfigParser()
    config.read(jenkins.config_file)

    if len(servers) == 0:
        cfg_sections = config.sections()
    elif len(servers) == 1:
        key = _reset_key(config, servers[0])
        log.info(key)
        return
    else:
        cfg_sections = list(servers)

    for section in cfg_sections:
        if not config.has_option(section, "url"):
            log.debug("Section does not contain a url, skipping...")
            continue

        log.info("Resetting API key for {}".format(section))
        if _reset_key(config, section):
            success += 1
        else:
            fail += 1
            log.error("Failed to reset API key for {}".format(section))

    log.info("Update configurations complete.")
    log.info("Success: {}".format(success))
    log.info("Failed: {}".format(fail))


token.add_command(change)
token.add_command(init)
token.add_command(print_token)
token.add_command(reset)


def _require_jjb_ini(config):
    if not os.path.isfile(config):
        log.error("jenkins_jobs.ini not found in any of the search paths. " "Please provide one before proceeding.")
        sys.exit(1)
