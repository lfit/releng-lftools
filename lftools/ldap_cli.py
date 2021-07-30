# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2018 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Helper for INFO file generation."""

from __future__ import print_function

from subprocess import STDOUT, check_output


def helper_yaml4info(group):
    """Build yaml of committers for your INFO.yaml."""
    command = ["yaml4info", group]
    status = check_output(command, stderr=STDOUT).decode()
    return status
