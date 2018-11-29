# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2018 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Test deploy command."""

import os
import sys

import pytest
import responses
import requests

from lftools import cli
import lftools.nexus.release_docker_hub as rdh

def test_remove_http_from_url():
    """Test _remove_http_from_url."""
    test_url=[["192.168.1.1", "192.168.1.1"],
         ["192.168.1.1:8081", "192.168.1.1:8081"],
         ["http://192.168.1.1:8081/nexus", "192.168.1.1:8081/nexus"],
         ["192.168.1.1:8081/nexus/", "192.168.1.1:8081/nexus/"],
         ["http://192.168.1.1:8081/nexus", "192.168.1.1:8081/nexus"],
         ["https://192.168.1.1:8081/nexus", "192.168.1.1:8081/nexus"],
         ["https://192.168.1.1:8081/nexus/", "192.168.1.1:8081/nexus/"],
         ["http://www.goodnexussite.org:8081", "www.goodnexussite.org:8081"]]

    for url in test_url:
        assert rdh._remove_http_from_url(url[0]) == url[1]


def test_format_image_id():
    """Test _remove_http_from_url."""
    test_id=[["b9e15a5d1e1a", "b9e15a5d1e1a"],
         ["sha256:b9e15a5d1e1a", "b9e15a5d1e1a"],
         ["sha256:3450464d68", "3450464d68"],
         ["192.168.1.1:8081/nexus/", "192.168.1.1:8081/nexus/"],
         ["sha256:3450464d68c9443dedc8bfe3272a23e6441c37f707c42d32fee0ebdbcd319d2c", "3450464d68c9443dedc8bfe3272a23e6441c37f707c42d32fee0ebdbcd319d2c"]]

    for id in test_id:
        assert rdh._format_image_id(id[0]) == id[1]
