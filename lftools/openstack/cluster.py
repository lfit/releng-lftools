# -*- coding: utf-8 -*-
# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2025 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""COE cluster related sub-commands for openstack command."""

__author__ = "Anil Belur"

import logging
import sys
from datetime import datetime, timedelta

import openstack
import openstack.config
from openstack.cloud.exc import OpenStackCloudException

log = logging.getLogger(__name__)


def _filter_clusters(clusters, days=0):
    """Filter cluster data and return list.

    :arg list clusters: List of cluster objects
    :arg int days: Filter clusters older than number of days
    :returns: Filtered list of clusters
    """
    filtered = []
    for cluster in clusters:
        # Handle different timestamp formats
        try:
            created_time = datetime.strptime(cluster.created_at, "%Y-%m-%dT%H:%M:%SZ")
        except (ValueError, AttributeError):
            try:
                created_time = datetime.strptime(cluster.created_at, "%Y-%m-%dT%H:%M:%S.%f")
            except (ValueError, AttributeError):
                # Skip if we can't parse the date
                continue

        if days and (created_time >= datetime.now() - timedelta(days=days)):
            continue

        filtered.append(cluster)
    return filtered


def list(os_cloud, days=0):
    """List COE clusters found according to parameters.

    :arg str os_cloud: Cloud name as defined in OpenStack clouds.yaml
    :arg int days: Filter clusters older than number of days (default: 0 = all)
    """
    cloud = openstack.connection.from_config(cloud=os_cloud)
    clusters = cloud.list_coe_clusters()

    filtered_clusters = _filter_clusters(clusters, days)
    for cluster in filtered_clusters:
        log.info(cluster.name)


def cleanup(os_cloud, days=0):
    """Remove clusters from cloud.

    :arg str os_cloud: Cloud name as defined in OpenStack clouds.yaml
    :arg int days: Filter clusters that are older than number of days
    """

    def _remove_clusters_from_cloud(clusters, cloud):
        log.info(f"Removing {len(clusters)} clusters from {cloud.cloud_config.name}.")
        for cluster in clusters:
            try:
                # COE clusters use UUID, delete by ID
                result = cloud.delete_coe_cluster(cluster.uuid)
            except OpenStackCloudException as e:
                if str(e).startswith("Multiple matches found for"):
                    log.warning(f"{str(e)}. Skipping cluster...")
                    continue
                else:
                    log.error(f"Unexpected exception: {str(e)}")
                    raise

            if not result:
                log.warning(
                    f'Failed to remove "{cluster.name}" from {cloud.cloud_config.name}. ' f"Possibly already deleted."
                )
            else:
                log.info(f'Removed "{cluster.name}" from {cloud.cloud_config.name}.')

    cloud = openstack.connection.from_config(cloud=os_cloud)
    clusters = cloud.list_coe_clusters()
    filtered_clusters = _filter_clusters(clusters, days)
    _remove_clusters_from_cloud(filtered_clusters, cloud)


def remove(os_cloud, cluster_name, minutes=0):
    """Remove a cluster from cloud.

    :arg str os_cloud: Cloud name as defined in OpenStack clouds.yaml
    :arg str cluster_name: Name or UUID of cluster to remove
    :arg int minutes: Only delete cluster if it is older than number of minutes
    """
    cloud = openstack.connection.from_config(cloud=os_cloud)
    cluster = cloud.get_coe_cluster(cluster_name)

    if not cluster:
        log.error("Cluster not found.")
        sys.exit(1)

    # Parse created_at timestamp
    try:
        created_time = datetime.strptime(cluster.created_at, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        try:
            created_time = datetime.strptime(cluster.created_at, "%Y-%m-%dT%H:%M:%S.%f")
        except ValueError:
            log.error("Unable to parse cluster creation time.")
            sys.exit(1)

    if minutes > 0 and created_time >= datetime.utcnow() - timedelta(minutes=minutes):
        log.warning(f'Cluster "{cluster.name}" is not older than {minutes} minutes.')
    else:
        cloud.delete_coe_cluster(cluster.uuid)
        log.info(f'Deleted cluster "{cluster.name}".')


def show(os_cloud, cluster_name):
    """Show details of a specific cluster.

    :arg str os_cloud: Cloud name as defined in OpenStack clouds.yaml
    :arg str cluster_name: Name or UUID of cluster
    """
    cloud = openstack.connection.from_config(cloud=os_cloud)
    cluster = cloud.get_coe_cluster(cluster_name)

    if not cluster:
        log.error("Cluster not found.")
        sys.exit(1)

    # Pretty print cluster details
    cloud.pprint(cluster)
