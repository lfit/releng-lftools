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

import logging

log = logging.getLogger(__name__)


def create_repo_target_regex(group_id):
    """Create a repo_target for Nexus use."""
    return '^/{}/.*'.format(group_id.replace('.', '[/\.]'))
