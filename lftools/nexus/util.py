# -*- code: utf-8 -*-
# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2018 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Utility functions for Nexus."""

__author__ = 'Thanh Ha'

from builtins import input
import logging
import re

log = logging.getLogger(__name__)


def create_repo_target_regex(group_id):
    """Create a repo_target for Nexus use."""
    return '^/{}/.*'.format(group_id.replace('.', '[/\.]'))


def gate_deletion(total_to_delete):
    """Prompt user for confirmation before deleting images."""
    while True:
        user_input = input("Would you like to delete all "
                           + str(total_to_delete)
                           + " images listed above? [y/N]: ")
        if not user_input or re.search(r"^[nN]", user_input):
            return False
        if re.search(r"^[yY]", user_input):
            return True
