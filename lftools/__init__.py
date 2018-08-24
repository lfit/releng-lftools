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

import logging
import logging.config

formatter = logging.Formatter('(%(levelname)s) %(name)s: %(message)s')
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logging.getLogger("").setLevel(logging.INFO)
logging.getLogger("").addHandler(console_handler)
