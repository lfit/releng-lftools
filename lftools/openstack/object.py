# -*- code: utf-8 -*-
# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Object related sub-commands for openstack command."""

__author__ = "Thanh Ha"

import shade


def list_containers(os_cloud):
    """List volumes found according to parameters."""
    cloud = shade.openstack_cloud(cloud=os_cloud)
    containers = cloud.list_containers()

    for container in containers:
        print(container)
