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
__version__ = '0.7.0-dev'

import logging
import logging.config
import os

def find_log_ini( file_name ):
  homedir = os.path.expanduser('~')
  log_file_home = os.path.abspath(os.path.join(homedir, ".config/lftools", file_name))
  log_file_etc = os.path.abspath(os.path.join("/etc/lftools", file_name))
  if os.path.exists(log_file_home):
      file_path = log_file_home
  elif os.path.exists(log_file_etc):
      file_path = log_file_etc
  else:
      file_path=('etc/%s' % file_name)
  return file_path

log_ini_file = "logging.ini"
log_ini_file_path = find_log_ini(log_ini_file)

logging.config.fileConfig(log_ini_file_path)
log = logging.getLogger(__name__)

log.info("Using logger config file: %s" % log_ini_file_path)
