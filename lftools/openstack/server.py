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
"""Server related sub-commands for openstack command."""

__author__ = 'Thanh Ha'

from datetime import datetime
from datetime import timedelta

import shade


def _filter_servers(servers, days=0):
    """Filter server data and return list."""
    filtered = []
    for server in servers:
        if days and (
                datetime.strptime(server.created, '%Y-%m-%dT%H:%M:%SZ')
                >= datetime.now() - timedelta(days=days)):
            continue

        filtered.append(server)
    return filtered


def list(os_cloud, days=0):
    """List servers found according to parameters."""
    cloud = shade.openstack_cloud(cloud=os_cloud)
    servers = cloud.list_servers()

    filtered_servers = _filter_servers(servers, days)
    for server in filtered_servers:
        print(server.name)


def cleanup(os_cloud, days=0, clouds=None):
    """Remove server from cloud.

    :arg str os_cloud: Cloud name as defined in OpenStack clouds.yaml.
    :arg int days: Filter servers that are older than number of days.
    :arg str clouds: If passed, comma-separated list of clouds to remove servers
        from. Otherwise os_cloud will be used.
    """
    def _remove_servers_from_cloud(servers, cloud):
        print('Removing {} servers from {}.'.format(len(servers), cloud.cloud_config.name))
        for server in servers:
            try:
                result = cloud.delete_server(server.name)
            except shade.exc.OpenStackCloudException as e:
                if str(e).startswith('Multiple matches found for'):
                    print('WARNING: {}. Skipping server...'.format(str(e)))
                    continue
                else:
                    print('ERROR: Unexpected exception: {}'.format(str(e)))
                    raise

            if not result:
                print('WARNING: Failed to remove \"{}\" from {}. Possibly already deleted.'
                      .format(server.name, cloud.cloud_config.name))
            else:
                print('Removed "{}" from {}.'.format(server.name, cloud.cloud_config.name))

    cloud = shade.openstack_cloud(cloud=os_cloud)
    if clouds:
        cloud_list = []
        for c in clouds.split(","):
            cloud_list.append(shade.openstack_cloud(cloud=c))

    servers = cloud.list_servers()
    filtered_servers = _filter_servers(servers, days)

    if clouds:
        for c in cloud_list:
            _remove_servers_from_cloud(filtered_servers, c)
    else:
        _remove_servers_from_cloud(filtered_servers, cloud)
