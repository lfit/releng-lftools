# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Exceptions for the API client."""
from __future__ import annotations


class UnsupportedRequestType(Exception):
    """Except on an unknown request."""

    def __str__(self) -> str:
        """Except unknown return type."""
        return "Unknown request type"
