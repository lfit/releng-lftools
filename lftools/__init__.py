# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2017, 2023 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# Contributors:
#   Thanh Ha - Initial implementation
#   Linux Foundation Release Engineering
##############################################################################
"""lftools package."""
from __future__ import annotations

__author__ = "Thanh Ha"
__summary__ = "Linux Foundation Release Engineering Tools"

import logging
import sys


class LogFormatter(logging.Formatter):
    """Custom log formatter."""

    default_fmt: logging.Formatter = logging.Formatter("%(levelname)s: %(message)s")
    debug_fmt: logging.Formatter = logging.Formatter("%(levelname)s: %(name)s:%(lineno)d: %(message)s")
    info_fmt: logging.Formatter = logging.Formatter("%(message)s")

    def format(self, record: logging.LogRecord) -> str:
        """Format log messages depending on log level."""
        if record.levelno == logging.INFO:
            return self.info_fmt.format(record)
        if record.levelno == logging.DEBUG:
            return self.debug_fmt.format(record)
        else:
            return self.default_fmt.format(record)


console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(LogFormatter())
logging.getLogger("").setLevel(logging.INFO)
logging.getLogger("").addHandler(console_handler)
