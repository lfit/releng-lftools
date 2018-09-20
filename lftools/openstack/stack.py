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

import logging
import sys
import time

import shade

from lftools.jenkins import Jenkins

log = logging.getLogger(__name__)


def create(os_cloud, name, template_file, parameter_file, timeout=900, tries=2):
    """Create a heat stack from a template_file and a parameter_file."""
    cloud = shade.openstack_cloud(cloud=os_cloud)
    stack_success = False

    print('Creating stack {}'.format(name))
    for i in range(tries):
        try:
            stack = cloud.create_stack(
                name,
                template_file=template_file,
                environment_files=[parameter_file],
                timeout=timeout,
                rollback=False)
        except shade.exc.OpenStackCloudHTTPError as e:
            if cloud.search_stacks(name):
                print('Stack with name {} already exists.'.format(name))
            else:
                print(e)
            sys.exit(1)

        stack_id = stack.id
        t_end = time.time() + timeout
        while time.time() < t_end:
            time.sleep(10)
            stack = cloud.get_stack(stack_id)

            if stack.stack_status == 'CREATE_IN_PROGRESS':
                print('Waiting to initialize infrastructure...')
            elif stack.stack_status == 'CREATE_COMPLETE':
                print('Stack initialization successful.')
                stack_success = True
                break
            elif stack.stack_status == 'CREATE_FAILED':
                print('WARN: Failed to initialize stack. Reason: {}'.format(
                    stack.stack_status_reason))
                if delete(os_cloud, stack_id):
                    break
            else:
                print('Unexpected status: {}'.format(stack.stack_status))

        if stack_success:
            break

    print('------------------------------------')
    print('Stack Details')
    print('------------------------------------')
    cloud.pprint(stack)
    print('------------------------------------')


def delete(os_cloud, name_or_id, timeout=900):
    """Delete a stack.

    Return True if delete was successful.
    """
    cloud = shade.openstack_cloud(cloud=os_cloud)
    print('Deleting stack {}'.format(name_or_id))
    cloud.delete_stack(name_or_id)

    t_end = time.time() + timeout
    while time.time() < t_end:
        time.sleep(10)
        stack = cloud.get_stack(name_or_id)

        if not stack or stack.stack_status == 'DELETE_COMPLETE':
            print('Successfully deleted stack {}'.format(name_or_id))
            return True
        elif stack.stack_status == 'DELETE_IN_PROGRESS':
            print('Waiting for stack to delete...')
        elif stack.stack_status == 'DELETE_FAILED':
            print('WARN: Failed to delete $STACK_NAME. Reason: {}'.format(
                stack.stack_status_reason))
            print('Retrying delete...')
            cloud.delete_stack(name_or_id)
        else:
            print('WARN: Unexpected delete status: {}'.format(
                stack.stack_status))
            print('Retrying delete...')
            cloud.delete_stack(name_or_id)

    print('Failed to delete stack.')
    return False


def delete_stale(os_cloud, jenkins_servers):
    """Search Jenkins and OpenStack for orphaned stacks and remove them.

    An orphaned stack is a stack that is not known in any of the Jenkins
    servers passed into this function.
    """
    cloud = shade.openstack_cloud(cloud=os_cloud)
    stacks = cloud.search_stacks()
    if not stacks:
        log.debug('No stacks to delete.')
        sys.exit(0)

    builds = []
    for server in jenkins_servers:
        jenkins = Jenkins(server)
        jenkins_url = jenkins.url.rstrip('/')
        silo = jenkins_url.split('/')

        if len(silo) == 4:  # https://jenkins.opendaylight.org/releng
            silo = silo[3]
        elif len(silo) == 3:  # https://jenkins.onap.org
            silo = 'production'
        else:
            log.error('Unexpected URL pattern, could not detect silo.')
            sys.exit(1)

        log.debug('Fetching running builds from {}'.format(jenkins_url))
        running_builds = jenkins.server.get_running_builds()
        for build in running_builds:
            build_name = '{}-{}-{}'.format(
                silo, build.get('name'), build.get('number'))
            log.debug('    {}'.format(build_name))
            builds.append(build_name)

    log.debug('Active stacks')
    for stack in stacks:
        if (stack.stack_status == 'CREATE_COMPLETE' or
                stack.stack_status == 'CREATE_FAILED' or
                stack.stack_status == 'DELETE_FAILED'):
            log.debug('    {}'.format(stack.stack_name))

            if stack.stack_status == 'DELETE_FAILED':
                cloud.pprint(stack)

            if stack.stack_name not in builds:
                log.debug('        >>>> Marked for deletion <<<<')
                delete(os_cloud, stack.stack_name)

        else:
            continue
