# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# Contributors:
#   Thanh Ha - Initial implementation
##############################################################################
"""lftools package."""

__author__ = 'Thanh Ha'
__summary__ = 'Linux Foundation Release Engineering Tools'
__version__ = '0.15.0'

import logging
import logging.config
import os
import sys

log = logging.getLogger(__name__)


def find_log_ini(file_name='logging.ini'):
    """Find the logging.ini file.

    Precedence:
        1) ~/.config/lftools/logging.ini
        2) /etc/lftools/logging.ini
        3) sys.prefix/etc/logging.ini

        Dev only...
        4) etc/logging.ini (Default fallback in dev environments)
    """
    homedir = os.path.expanduser('~')
    log_file_etc = os.path.abspath(os.path.join('/etc', 'lftools', file_name))
    log_file_home = os.path.abspath(os.path.join(homedir, '.config', 'lftools', file_name))
    log_file_pyprefix = os.path.abspath(os.path.join(sys.prefix, 'etc', file_name))

    if os.path.exists(log_file_home):
        file_path = log_file_home
    elif os.path.exists(log_file_etc):
        file_path = log_file_etc
    elif os.path.exists(log_file_pyprefix):
        file_path = log_file_pyprefix
    else:
        file_path = os.path.join('etc', file_name)
    return file_path


log_ini_file = find_log_ini()

if os.path.exists(log_ini_file):
    logging.config.fileConfig(log_ini_file)
    log.info("Using logger config file {}".format(log_ini_file))
else:
    formatter = logging.Formatter('%(asctime)s (%(levelname)s) %(name)s: %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logging.getLogger("").setLevel(logging.NOTSET)
    logging.getLogger("").addHandler(console_handler)
    log.info("Log ini file not found. Using a default logger...")
