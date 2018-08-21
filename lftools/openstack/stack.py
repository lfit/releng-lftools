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

import sys
import time

import shade


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
