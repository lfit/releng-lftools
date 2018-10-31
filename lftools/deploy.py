# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Library of functions for deploying artifacts to Nexus."""

import glob
import logging
import os
import shutil


log = logging.getLogger(__name__)


def copy_archives(workspace, pattern=None):
    """Copy files matching PATTERN in a WORKSPACE to the current directory.

    The best way to use this function is to cd into the directory you wish to
    store the files first before calling the function.
    """
    archives_dir = os.path.join(workspace, 'archives')
    dest_dir = os.getcwd()

    log.debug('Copying files from {} with pattern \'{}\' to {}.'.format(
        workspace, pattern, dest_dir))
    for file_or_dir in os.listdir(archives_dir):
        f = os.path.join(archives_dir, file_or_dir)
        try:
            log.debug('Moving {}.'.format(f))
            #shutil.move(f, dest_dir)
        except shutil.Error as e:
            log.warn(e)

    paths = []
    for p in pattern:
        search = os.path.join(workspace, p)
        paths.extend(glob.glob(search, recursive=True))
    log.debug('Files found: {}'.format(paths))

    # for path in paths copy files while recreating dir structure
    # exclude filenames that are over 255 characters
