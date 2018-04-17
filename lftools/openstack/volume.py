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
"""volume related sub-commands for openstack command."""

__author__ = 'Thanh Ha'

from datetime import datetime
from datetime import timedelta
import sys

import shade


def _filter_volumes(volumes, days=0):
    """Filter volume data and return list."""
    filtered = []
    for volume in volumes:
        if days and (
                datetime.strptime(volume.created_at, '%Y-%m-%dT%H:%M:%S.%f')
                >= datetime.now() - timedelta(days=days)):
            continue

        filtered.append(volume)
    return filtered


def list(os_cloud, days=0):
    """List volumes found according to parameters."""
    cloud = shade.openstack_cloud(cloud=os_cloud)
    volumes = cloud.list_volumes()

    filtered_volumes = _filter_volumes(volumes, days)
    for volume in filtered_volumes:
        print(volume.name)


def cleanup(os_cloud, days=0):
    """Remove volume from cloud.

    :arg str os_cloud: Cloud name as defined in OpenStack clouds.yaml.
    :arg int days: Filter volumes that are older than number of days.
    """
    def _remove_volumes_from_cloud(volumes, cloud):
        print('Removing {} volumes from {}.'.format(len(volumes), cloud.cloud_config.name))
        for volume in volumes:
            try:
                result = cloud.delete_volume(volume.name)
            except shade.exc.OpenStackCloudException as e:
                if str(e).startswith('Multiple matches found for'):
                    print('WARNING: {}. Skipping volume...'.format(str(e)))
                    continue
                else:
                    print('ERROR: Unexpected exception: {}'.format(str(e)))
                    raise

            if not result:
                print('WARNING: Failed to remove \"{}\" from {}. Possibly already deleted.'
                      .format(volume.name, cloud.cloud_config.name))
            else:
                print('Removed "{}" from {}.'.format(volume.name, cloud.cloud_config.name))

    cloud = shade.openstack_cloud(cloud=os_cloud)
    volumes = cloud.list_volumes()
    filtered_volumes = _filter_volumes(volumes, days)
    _remove_volumes_from_cloud(filtered_volumes, cloud)


def remove(os_cloud, volume_name, minutes=0):
    """Remove a volume from cloud.

    :arg str os_cloud: Cloud name as defined in OpenStack clouds.yaml.
    :arg int minutes: Only delete volume if it is older than number of minutes.
    """
    cloud = shade.openstack_cloud(cloud=os_cloud)
    volume = cloud.get_volume(volume_name)

    if not volume:
        print("ERROR: volume not found.")
        sys.exit(1)

    if (datetime.strptime(volume.created_at, '%Y-%m-%dT%H:%M:%S.%f')
            >= datetime.utcnow() - timedelta(minutes=minutes)):
        print('WARN: volume "{}" is not older than {} minutes.'.format(
            volume.name, minutes))
    else:
        cloud.delete_volume(volume.name)
