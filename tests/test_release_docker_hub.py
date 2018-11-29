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


def test_tag_class_valid_tags():
    """Test TagClass"""
    org = 'onap'
    repo = 'base/sdc-sanity'
    test_tags =["1.2.3", "1.22.333", "111.22.3", "10.11.12", "1.0.3"]
    rdh.initialize (org)
    tags = rdh.TagClass (org, repo)
    for tag in test_tags:
        tags.add_tag(tag)
    assert len(tags.valid) == len(test_tags)
    assert len(tags.invalid) == 0

def test_tag_class_invalid_tags():
    """Test TagClass"""
    org = 'onap'
    repo = 'base/sdc-sanity'
    test_tags =["v1.2.3", "1.22", "111.22.3a", "10.11.12.3", "draft",
        "1.2.jan14", "1.2.3.4.5.6.7.8", "1", "latest", "v0.1.0",
        "1.1-20170906T011834", "2.0-20180221T152423",
        "1.3.0-20181121T1329", "1.1.2-SNAPSHOT-20181231T234559Z",
        "1.1.2-STAGING-20181231T234559Z"]
    rdh.initialize (org)
    tags = rdh.TagClass (org, repo)
    for tag in test_tags:
        tags.add_tag(tag)
    assert len(tags.invalid) == len(test_tags)
    assert len(tags.valid) == 0

def test_tag_class_repository_exist():
    """Test TagClass"""
    org = 'onap'
    repo = 'base/sdc-sanity'
    rdh.initialize (org)
    tags = rdh.TagClass (org, repo)
    assert tags.repository_exist == True

def test_nexus_tag_class(responses):
    """Test NexusTagClass"""
    org = 'onap'
    repo = 'base/sdc-sanity'
    url = 'https://nexus3.onap.org:10002/v2/onap/base/sdc-sanity/tags/list'
    answer = '{"name":"onap/base_sdc-sanity","tags":["latest","1.3.0","1.3.1","1.4.0","1.4.1","v1.0.0"]}'
    answer_valid_tags = ["1.3.0","1.3.1","1.4.0","1.4.1"]
    answer_invalid_tags = ["latest", "v1.0.0" ]
    responses.add(responses.GET, url, body=answer, status=200)
    rdh.initialize (org)
    test_tags = rdh.NexusTagClass (org, repo)
    for tag in answer_valid_tags:
        assert tag in test_tags.valid
    for tag in answer_invalid_tags:
        assert tag in test_tags.invalid
    assert len(test_tags.valid) == len(answer_valid_tags)
    assert len(test_tags.invalid) == len(answer_invalid_tags)


def test_docker_tag_class(responses):
    """Test DockerTagClass"""
    org = 'onap'
    repo = 'base-sdc-sanity'
    url = 'https://registry.hub.docker.com/v1/repositories/onap/base-sdc-sanity/tags'
    answer = """[{"layer": "", "name": "latest"},
        {"layer": "", "name": "1.3.0"},
        {"layer": "", "name": "1.3.1"},
        {"layer": "", "name": "1.4.0"},
        {"layer": "", "name": "1.4.1"},
        {"layer": "", "name": "v1.0.0"}]
    """
    answer_valid_tags = ["1.3.0","1.3.1","1.4.0","1.4.1"]
    answer_invalid_tags = ["latest", "v1.0.0"]
    responses.add(responses.GET, url, body=answer, status=200)
    rdh.initialize (org)
    test_tags = rdh.DockerTagClass (org, repo)
    for tag in answer_valid_tags:
        assert tag in test_tags.valid
    for tag in answer_invalid_tags:
        assert tag in test_tags.invalid
    assert len(test_tags.valid) == len(answer_valid_tags)
    assert len(test_tags.invalid) == len(answer_invalid_tags)
