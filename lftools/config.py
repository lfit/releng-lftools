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


import configparser
import logging
import os.path
import sys

from xdg import XDG_CONFIG_HOME

log = logging.getLogger(__name__)

LFTOOLS_CONFIG_FILE = os.path.join(XDG_CONFIG_HOME, "lftools", "lftools.ini")


def get_config():
    """Get the config object."""
    config = configparser.ConfigParser()  # noqa
    config.read(LFTOOLS_CONFIG_FILE)
    return config


def has_section(section):
    """Get a configuration from a section."""
    config = get_config()
    return config.has_section(section)


def get_setting(section, option=None):
    """Get a configuration from a section."""
    sys.tracebacklimit = 0
    config = get_config()

    if option:
        try:
            return config.get(section, option)
        except (configparser.NoOptionError, configparser.NoSectionError) as e:
            raise e

    else:
        try:
            return config.options(section)
        except configparser.NoSectionError as e:
            raise e


def set_setting(section, option, value):
    """Save a configuration setting to config file."""
    config = get_config()
    config.set(section, option, value)

    with open(LFTOOLS_CONFIG_FILE, "w") as configfile:
        config.write(configfile)
