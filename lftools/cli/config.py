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


import click

from lftools import config


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
    result = config.get_setting(section, option)
    if isinstance(result, list):
        for i in result:
            print('{}: {}'.format(i, config.get_setting(section, i)))
    else:
        print(result)


@click.command(name='set')
@click.argument('section')
@click.argument('option')
@click.argument('value')
@click.pass_context
def set_setting(ctx, section, option, value):
    """Set a setting in the config file."""
    config.set_setting(section, option, value)


config_sys.add_command(get_setting)
config_sys.add_command(set_setting)
