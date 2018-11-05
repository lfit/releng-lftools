# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2018 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""CLI interface for config subsystem."""

__author__ = 'Thanh Ha'

import logging
import sys

import click
from six.moves import configparser

from lftools import config

log = logging.getLogger(__name__)


@click.group(name='config')
@click.pass_context
def config_sys(ctx):
    """Configuration subsystem."""
    pass


@click.command(name='get')
@click.argument('section', type=str)
@click.argument('option', type=str, required=False)
@click.pass_context
def get_setting(ctx, section, option):
    """Print section or setting from config file."""
    try:
        result = config.get_setting(section, option)
    except (configparser.NoOptionError,
            configparser.NoSectionError) as e:
        log.error(e)
        sys.exit(1)

    if isinstance(result, list):
        for i in result:
            log.info('{}: {}'.format(i, config.get_setting(section, i)))
    else:
        log.info(result)


@click.command(name='set')
@click.argument('section')
@click.argument('option')
@click.argument('value')
@click.pass_context
def set_setting(ctx, section, option, value):
    """Set a setting in the config file."""
    log.debug('Set config\n[{}]\n{}:{}'.format(section, option, value))
    config.set_setting(section, option, value)


config_sys.add_command(get_setting)
config_sys.add_command(set_setting)
