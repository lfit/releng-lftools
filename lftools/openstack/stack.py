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
"""stack related sub-commands for openstack command."""

__author__ = 'Thanh Ha'

import time

import shade


def create(os_cloud, name, template_file, parameter_file, timeout=900, tries=2):
    cloud = shade.openstack_cloud(cloud=os_cloud)


    print('Creating {}'.format(name))
    for i in range(tries):
        cloud.create_stack(
            name,
            template_file=template_file,
            environment_files=[parameter_file],
            timeout=timeout,
            rollback=False)

        t_end = time.time() + timeout
        while time.time() < t_end:
            time.sleep(60)
