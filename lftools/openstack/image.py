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

__author__ = "Thanh Ha"

import logging
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta

import openstack
import openstack.config
from openstack.cloud.exc import OpenStackCloudException
from six.moves import urllib

log = logging.getLogger(__name__)


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
        if ci_managed and image.metadata.get("ci_managed", None) != "yes":
            continue
        if image.protected:
            continue
        if days and (
            datetime.strptime(image.created_at, "%Y-%m-%dT%H:%M:%SZ") >= datetime.now() - timedelta(days=days)
        ):
            continue

        filtered.append(image)
    return filtered


def list(os_cloud, days=0, hide_public=False, ci_managed=True):
    """List images found according to parameters."""
    cloud = openstack.connection.from_config(cloud=os_cloud)
    images = cloud.list_images()

    filtered_images = _filter_images(images, days, hide_public, ci_managed)
    for image in filtered_images:
        log.info(image.name)


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
        log.info("Removing {} images from {}.".format(len(images), cloud.config._name))
        project_info = cloud._get_project_info()
        for image in images:
            if image.is_protected:
                log.warning("Image {} is protected. Cannot remove...".format(image.name))
                continue

            if image.visibility == "shared":
                log.warning("Image {} is shared. Cannot remove...".format(image.name))
                continue

            if project_info["id"] != image.owner:
                log.warning("Image {} not owned by project {}. Cannot remove...".format(image.name, cloud.config._name))
                continue

            try:
                result = cloud.delete_image(image.name)
            except OpenStackCloudException as e:
                if str(e).startswith("Multiple matches found for"):
                    log.warning("{}. Skipping image...".format(str(e)))
                    continue
                else:
                    log.error("Unexpected exception: {}".format(str(e)))
                    raise

            if not result:
                log.warning(
                    'Failed to remove "{}" from {}. Possibly already deleted.'.format(image.name, cloud.config._name)
                )
            else:
                log.info('Removed "{}" from {}.'.format(image.name, cloud.config._name))

    cloud_list = []
    if clouds:
        for c in clouds.split(","):
            cloud_list.append(c)

    if os_cloud not in cloud_list:
        cloud_list.append(os_cloud)

    for c in cloud_list:
        cloud = openstack.connection.from_config(cloud=c)
        images = cloud.list_images()
        if images:
            filtered_images = _filter_images(images, days, hide_public, ci_managed)
        if filtered_images:
            _remove_images_from_cloud(filtered_images, cloud)


def share(os_cloud, image, clouds):
    """Share image with another tenant."""

    def _get_image_id(os_cloud, image):
        cmd = ["openstack", "--os-cloud", os_cloud, "image", "list", "--name", image, "-f", "value", "-c", "ID"]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        log.debug("exit code: {}".format(p.returncode))
        log.debug(stderr.decode("utf-8"))
        if p.returncode:
            sys.exit(1)

        image_id = stdout.decode("utf-8").strip()
        log.debug("image_id: {}".format(image_id))
        return image_id

    def _mark_image_shared(os_cloud, image):
        cmd = ["openstack", "--os-cloud", os_cloud, "image", "set", "--shared", image]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        log.debug("exit code: {}".format(p.returncode))
        log.debug(stderr.decode("utf-8"))
        if p.returncode:
            sys.exit(1)

    def _get_token(cloud):
        cmd = ["openstack", "--os-cloud", cloud, "token", "issue", "-c", "project_id", "-f", "value"]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        log.debug("exit code: {}".format(p.returncode))
        log.debug(stderr.decode("utf-8"))
        if p.returncode:
            sys.exit(1)

        token = stdout.decode("utf-8").strip()
        log.debug("token: {}".format(token))
        return token

    def _share_to_cloud(os_cloud, image, token):
        log.debug("Sharing image {} to {}".format(image, token))
        cmd = ["openstack", "--os-cloud", os_cloud, "image", "add", "project", image, token]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        log.debug("exit code: {}".format(p.returncode))
        log.debug(stderr.decode("utf-8"))

        if p.returncode:
            if stderr.decode("utf-8").startswith("409 Conflict"):
                log.info("  Image is already shared.")
            else:
                sys.exit(1)

    def _accept_shared_image(cloud, image):
        log.debug("Accepting image {}".format(image))
        cmd = ["openstack", "--os-cloud", cloud, "image", "set", "--accept", image]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        log.debug("exit code: {}".format(p.returncode))
        log.debug(stderr.decode("utf-8"))
        if p.returncode:
            sys.exit(1)

    log.info('Marking {}\'s image "{}" as shared.'.format(os_cloud, image))
    image_id = _get_image_id(os_cloud, image)
    _mark_image_shared(os_cloud, image_id)

    for cloud in clouds:
        log.info("Sharing to {}.".format(cloud))
        _share_to_cloud(os_cloud, image_id, _get_token(cloud))
        _accept_shared_image(cloud, image_id)


def upload(os_cloud, image, name, disk_format="raw"):
    """Upload image to openstack."""
    log.info('Uploading image {} with name "{}".'.format(image, name))
    cloud = openstack.connection.from_config(cloud=os_cloud)

    if re.match(r"^http[s]?://", image):
        tmp = tempfile.NamedTemporaryFile(suffix=".img")
        log.info("URL provided downloading image locally to {}.".format(tmp.name))
        urllib.request.urlretrieve(image, tmp.name)  # nosec
        image = tmp.name

    try:
        cloud.create_image(name, image, disk_format=disk_format, wait=True)
    except FileNotFoundError as e:
        log.info(str(e))
        sys.exit(1)

    log.info("Upload complete.")
