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
from __future__ import annotations

import logging
import os.path
import sys
from configparser import ConfigParser, NoOptionError, NoSectionError
from typing import List, Optional

from xdg import XDG_CONFIG_HOME

log: logging.Logger = logging.getLogger(__name__)

LFTOOLS_CONFIG_FILE: str = os.path.join(XDG_CONFIG_HOME, "lftools", "lftools.ini")


def get_config() -> ConfigParser:
    """Get the config object."""
    config: ConfigParser = ConfigParser()  # noqa
    config.read(LFTOOLS_CONFIG_FILE)
    return config


def has_section(section: str) -> bool:
    """Get a configuration from a section."""
    config = get_config()
    return config.has_section(section)


def get_setting(section: str, option: Optional[str] = None) -> str | List[str]:
    """Get a configuration from a section."""
    sys.tracebacklimit = 0
    config: ConfigParser = get_config()

    if option:
        try:
            return config.get(section, option)
        except (NoOptionError, NoSectionError) as e:
            raise e

    else:
        try:
            return config.options(section)
        except NoSectionError as e:
            raise e


def set_setting(section: str, option: str, value: str) -> None:
    """Save a configuration setting to config file."""
    config: ConfigParser = get_config()
    config.set(section, option, value)

    with open(LFTOOLS_CONFIG_FILE, "w") as configfile:
        config.write(configfile)
