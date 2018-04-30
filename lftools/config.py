# -*- coding: utf-8 -*-
# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2018 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Configuration subsystem for lftools."""

__author__ = 'Thanh Ha'

import sys

from six.moves import configparser
from xdg import XDG_CONFIG_HOME

LFTOOLS_CONFIG_FILE = '/'.join([XDG_CONFIG_HOME, 'lftools', 'lftools.ini'])


def get_config():
    """Get the config object."""
    config = configparser.ConfigParser()
    config.read(LFTOOLS_CONFIG_FILE)
    return config


def get_setting(section, option=None):
    """Get a configuration from a section."""
    config = get_config()

    if option:
        try:
            return config.get(section, option)
        except configparser.NoOptionError:
            print('ERROR: Config option does not exist.')
            sys.exit(1)
        except configparser.NoSectionError:
            print('ERROR: Config section does not exist.')
            sys.exit(1)

    else:
        try:
            return config.options(section)
        except configparser.NoSectionError:
            print('ERROR: Config section does not exist.')
            sys.exit(1)


def set_setting(section, option, value):
    """Save a configuration setting to config file."""
    config = get_config()
    config.set(section, option, value)

    with open(LFTOOLS_CONFIG_FILE, 'w') as configfile:
        config.write(configfile)
