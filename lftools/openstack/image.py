# -*- code: utf-8 -*-
# @License EPL-1.0 <http://spdx.org/licenses/EPL-1.0>
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################

__author__ = 'Thanh Ha'

from datetime import datetime
from datetime import timedelta
import shade


def list(os_cloud, age_days=0):
    cloud = shade.openstack_cloud(cloud=os_cloud)
    images = cloud.list_images()

    for image in images:
        if not image.is_public:
            if datetime.strptime(image.created_at, '%Y-%m-%dT%H:%M:%SZ') < datetime.now()-timedelta(days=age_days):
                print(image.created_at, image.name)


def cleanup(os_cloud, age_days=0):
    cloud = shade.openstack_cloud(cloud=os_cloud)
    images = cloud.list_images()

    for image in images:
        if not image.is_public:
            if datetime.strptime(image.created_at, '%Y-%m-%dT%H:%M:%SZ') < datetime.now()-timedelta(days=age_days):
                # TODO: This should actually delete images.
                print(image.created_at, image.name)
