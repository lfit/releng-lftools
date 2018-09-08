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

__author__ = 'Thanh Ha'

import logging
import sys

import click
import requests
from six.moves import configparser

from lftools import config as lftools_cfg
from lftools.jenkins import JJB_INI
from lftools.jenkins.token import get_token

log = logging.getLogger(__name__)


@click.group()
@click.pass_context
def token(ctx):
    """Get API token."""


@click.command()
@click.pass_context
def change(ctx):
    """Generate a new API token."""
    log.info(get_token(ctx.obj['jenkins_url'], True))


@click.command()
@click.argument('name')
@click.argument('url')
def init(name, url):
    """Initialize jenkins_jobs.ini config for new server section."""
    _require_jjb_ini()

    config = configparser.ConfigParser()
    config.read(JJB_INI)

    token = get_token(url, True)
    try:
        config.add_section(name)
    except configparser.DuplicateSectionError as e:
        log.error(e)
        sys.exit(1)

    config.set(name, 'url', url)
    config.set(name, 'user', lftools_cfg.get_setting('global', 'username'))
    config.set(name, 'password', token)

    with open(JJB_INI, 'w') as configfile:
        config.write(configfile)


@click.command(name='print')
@click.pass_context
def print_token(ctx):
    """Print current API token."""
    log.info(get_token(ctx.obj['jenkins_url']))


@click.command()
@click.argument('server', required=False)
@click.pass_context
def reset(ctx, server):
    """Regenerate API tokens for all configurations in jenkins_jobs.ini."""
    _require_jjb_ini()

    def _reset_key(config, server):
        url = config.get(server, 'url')

        try:
            token = get_token(url, True)
            config.set(server, 'password', token)
            return token
        except requests.exceptions.ConnectionError as e:
            return None

    fail = 0
    success = 0
    config = configparser.ConfigParser()
    config.read(JJB_INI)

    if server:
        key = _reset_key(config, server)
        log.info(key)
        return

    for section in config.sections():
        if not config.has_option(section, 'url'):
            log.debug('Section does not contain a url, skipping...')
            continue

        log.info('Resetting API key for {}'.format(section))
        if _reset_key(config, section):
            success += 1
        else:
            fail += 1
            log.error('Failed to reset API key for {}'.format(section))

    with open(JJB_INI, 'w') as configfile:
        config.write(configfile)

    log.info('Update configurations complete.')
    log.info('Success: {}'.format(success))
    log.info('Failed: {}'.format(fail))


token.add_command(change)
token.add_command(init)
token.add_command(print_token)
token.add_command(reset)


def _require_jjb_ini():
    if not JJB_INI:
        log.error('jenkins_jobs.ini not found in any of the search paths. '
                  'Please provide one before proceeding.')
        sys.exit(1)
