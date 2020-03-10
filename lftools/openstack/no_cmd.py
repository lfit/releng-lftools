# -*- code: utf-8 -*-
# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""CLI configuration for openstack command."""

__author__ = "Thanh Ha"


import click


@click.group()
@click.pass_context
def openstack(ctx, os_cloud):
    """(lftools[openstack]) Provides an OpenStack interface.

    To activate this interface run `pip install lftools[openstack]`.
    """
    pass
