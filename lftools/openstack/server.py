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
"""Server related sub-commands for openstack command."""

__author__ = "Anil Belur"

import sys
from datetime import datetime, timedelta

import openstack
import openstack.config
from openstack.cloud.exc import OpenStackCloudException


def _filter_servers(servers, days=0):
    """Filter server data and return list."""
    filtered = []
    for server in servers:
        if days and (datetime.strptime(server.created, "%Y-%m-%dT%H:%M:%SZ") >= datetime.now() - timedelta(days=days)):
            continue

        filtered.append(server)
    return filtered


def list(os_cloud, days=0):
    """List servers found according to parameters."""
    cloud = openstack.connection.from_config(cloud=os_cloud)
    servers = cloud.list_servers()

    filtered_servers = _filter_servers(servers, days)
    for server in filtered_servers:
        print(server.name)


def cleanup(os_cloud, days=0):
    """Remove server from cloud.

    :arg str os_cloud: Cloud name as defined in OpenStack clouds.yaml.
    :arg int days: Filter servers that are older than number of days.
    """

    def _remove_servers_from_cloud(servers, cloud):
        print("Removing {} servers from {}.".format(len(servers), cloud.cloud_config.name))
        for server in servers:
            try:
                result = cloud.delete_server(server.name)
            except OpenStackCloudException as e:
                if str(e).startswith("Multiple matches found for"):
                    print("WARNING: {}. Skipping server...".format(str(e)))
                    continue
                else:
                    print("ERROR: Unexpected exception: {}".format(str(e)))
                    raise

            if not result:
                print(
                    'WARNING: Failed to remove "{}" from {}. Possibly already deleted.'.format(
                        server.name, cloud.cloud_config.name
                    )
                )
            else:
                print('Removed "{}" from {}.'.format(server.name, cloud.cloud_config.name))

    cloud = openstack.connection.from_config(cloud=os_cloud)
    servers = cloud.list_servers()
    filtered_servers = _filter_servers(servers, days)
    _remove_servers_from_cloud(filtered_servers, cloud)


def remove(os_cloud, server_name, minutes=0):
    """Remove a server from cloud.

    :arg str os_cloud: Cloud name as defined in OpenStack clouds.yaml.
    :arg int minutes: Only delete server if it is older than number of minutes.
    """
    cloud = openstack.connection.from_config(cloud=os_cloud)
    server = cloud.get_server(server_name)

    if not server:
        print("ERROR: Server not found.")
        sys.exit(1)

    if datetime.strptime(server.created, "%Y-%m-%dT%H:%M:%SZ") >= datetime.utcnow() - timedelta(minutes=minutes):
        print('WARN: Server "{}" is not older than {} minutes.'.format(server.name, minutes))
    else:
        cloud.delete_server(server.name)
