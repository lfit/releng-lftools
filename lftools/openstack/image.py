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
"""Image related sub-commands for openstack command."""

__author__ = 'Thanh Ha'

from datetime import datetime
from datetime import timedelta

import shade


def _filter_images(images, days=0, hide_public=False, ci_managed=True):
    """Filter image data and return list.

    :arg bool ci_managed: Filters images with metadata set to `ci_managed=yes`.
        (Default: true)
    :arg bool hide_public: Whether or not to include public images.
    """
    filtered = []
    for image in images:
        if hide_public and image.is_public:
            continue
        if ci_managed and image.metadata.get('ci_managed', None) != 'yes':
            continue
        if image.protected:
            continue
        if days and (
                datetime.strptime(image.created_at, '%Y-%m-%dT%H:%M:%SZ')
                >= datetime.now() - timedelta(days=days)):
            continue

        filtered.append(image)
    return filtered


def list(os_cloud, days=0, hide_public=False, ci_managed=True):
    """List images found according to parameters."""
    cloud = shade.openstack_cloud(cloud=os_cloud)
    images = cloud.list_images()

    filtered_images = _filter_images(images, days, hide_public, ci_managed)
    for image in filtered_images:
        print(image.name)


def cleanup(os_cloud, days=0, hide_public=False, ci_managed=True, clouds=None):
    """Remove image from cloud.

    :arg str os_cloud: Cloud name as defined in OpenStack clouds.yaml.
    :arg bool ci_managed: Filters images with metadata set to `ci_managed=yes`.
        (Default: true)
    :arg int days: Filter images that are older than number of days.
    :arg bool hide_public: If true, will ignore public images. (Default: false)
    :arg str clouds: If passed, comma-separated list of clouds to remove image
        from. Otherwise os_cloud will be used.
    """
    def _remove_images_from_cloud(images, cloud):
        print('Removing {} images from {}.'.format(len(images), cloud.cloud_config.name))
        for image in images:
            if image.is_protected:
                print('WARNING: Image {} is protected. Cannot remove...'.format(image.name))
                continue

            try:
                result = cloud.delete_image(image.name)
            except shade.exc.OpenStackCloudException as e:
                if str(e).startswith('Multiple matches found for'):
                    print('WARNING: {}. Skipping image...'.format(str(e)))
                    continue
                else:
                    print('ERROR: Unexpected exception: {}'.format(str(e)))
                    raise

            if not result:
                print('WARNING: Failed to remove \"{}\" from {}. Possibly already deleted.'
                      .format(image.name, cloud.cloud_config.name))
            else:
                print('Removed "{}" from {}.'.format(image.name, cloud.cloud_config.name))

    cloud = shade.openstack_cloud(cloud=os_cloud)
    if clouds:
        cloud_list = []
        for c in clouds.split(","):
            cloud_list.append(shade.openstack_cloud(cloud=c))

    images = cloud.list_images()
    filtered_images = _filter_images(images, days, hide_public, ci_managed)

    if clouds:
        for c in cloud_list:
            _remove_images_from_cloud(filtered_images, c)
    else:
        _remove_images_from_cloud(filtered_images, cloud)
