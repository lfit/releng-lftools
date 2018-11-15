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
"""Utility functions for Nexus."""

__author__ = 'Thanh Ha'

import logging
import re
import sys

from deb_pkg_tools.package import inspect_package_fields
import rpmfile

log = logging.getLogger(__name__)


def create_repo_target_regex(group_id):
    """Create a repo_target for Nexus use."""
    return '^/{}/.*'.format(group_id.replace('.', '[/\.]'))


def find_packaging_from_file_name(file_name):
    """Find packaging type based on file extension."""
    if file_name.endswith(".tar.gz"):
        packaging = "tar.gz"
    else:
        ext_index = file_name.rfind(".")
        if ext_index == -1:
            log.error("ERROR: Could not determine packaging type. Please "
                      "provide an appropriate \"packaging\" parameter.")
            sys.exit(1)
        packaging = file_name[ext_index+1:]
    return packaging


def get_info_from_rpm(path):
    """Return data pulled from the headers of an RPM file."""
    info = {}
    rpm = rpmfile.open(path)
    info["name"] = rpm.headers.get("name")
    ver = rpm.headers.get("version")
    if re.search('\.s(rc\.)?rpm', path):
        info["version"] = "{}.{}".format(ver, "src")
    else:
        info["version"] = "{}.{}".format(ver, rpm.headers.get("arch"))
    log.debug("Info from rpm: {}".format(info))
    return info


def get_info_from_deb(path):
    """Return data pulled from a deb archive."""
    info = {}
    data = inspect_package_fields(path)
    info["name"] = data["Package"]
    info["version"] = data["Version"]
    log.debug("Info from deb: {}".format(info))
    return info
