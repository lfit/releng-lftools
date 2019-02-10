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


class TestProjectClass:
    """Test ProjectClass.

    This class contains all the test cases for the ProjectClass.
    We mock the helper functions _docker_pull, _docker_tag, _docker_push, and
    _docker_cleanup. This means we do not have to do anything with the actual
    docker api.
    """

    _test_image_long_id = 'sha256:3450464d68c9443dedc8bfe3272a23e6441c37f707c42d32fee0ebdbcd319d2c'
    _test_image_short_id = 'sha256:3450464d68'
    _expected_nexus_image_str = ['nexus3.onap.org:10002/onap/base/sdc-sanity:1.4.0',
                                'nexus3.onap.org:10002/onap/base/sdc-sanity:1.4.1']

    class mock_image:
        id = ''
        short_id = ''
        def __init__(self, id, short_id):
            self.id = id
            self.short_id = short_id

    class count_mock_hits:
        pull = 0
        tag = 0
        push = 0
        cleanup = 0

    counter = count_mock_hits

    class nbr_exceptions:
        pull = 0
        tag = 0
        push = 0
        cleanup = 0

    nbr_exc = nbr_exceptions

    def mocked_docker_pull(self, nexus_image_str, count, tag, retry_text='', progbar=False):
        """Mocking Pull an image from Nexus."""
        if not nexus_image_str in self._expected_nexus_image_str:
            raise ValueError('Wrong nexus project in pull')
        image = self.mock_image (self._test_image_long_id, self._test_image_short_id)
        self.counter.pull = self.counter.pull + 1
        if self.counter.pull > self.nbr_exc.pull:
            return image
        else:
            raise requests.exceptions.ConnectionError('Connection Error')

    def mocked_docker_tag(self, count, image, tag, retry_text='', progbar=False):
        """Mocking Tag the image with proper docker name and version."""
        if not image.id == self._test_image_long_id:
            raise ValueError('Wrong image id in remove')
        if not tag in ["1.4.0","1.4.1"]:
            raise ValueError('Wrong tag in docker_tag')
        self.counter.tag = self.counter.tag + 1
        if self.counter.tag <= self.nbr_exc.tag:
            raise requests.exceptions.ConnectionError('Connection Error')

    def mocked_docker_push(self, count, image, tag, retry_text, progbar=False):
        """Mocking Tag the image with proper docker name and version."""
        if not image.id == self._test_image_long_id:
            raise ValueError('Wrong image id in remove')
        if not tag in ["1.4.0","1.4.1"]:
            raise ValueError('Wrong tag in push')
        self.counter.push = self.counter.push + 1
        if self.counter.push <= self.nbr_exc.push:
            raise requests.exceptions.ConnectionError('Connection Error')

    def mocked_docker_cleanup(self, count, image, tag, retry_text='', progbar=False):
        """Mocking Tag the image with proper docker name and version."""
        if not image.id == self._test_image_long_id:
            raise ValueError('Wrong image id in remove')
        self.counter.cleanup = self.counter.cleanup + 1
        if self.counter.cleanup <= self.nbr_exc.cleanup:
            raise requests.exceptions.ConnectionError('Connection Error')

    def test_ProjectClass_2_missing(self, responses, mocker):
        """Test ProjectClass"""
        mocker.patch('lftools.nexus.release_docker_hub.ProjectClass._docker_pull', side_effect=self.mocked_docker_pull)
        mocker.patch('lftools.nexus.release_docker_hub.ProjectClass._docker_tag', side_effect=self.mocked_docker_tag)
        mocker.patch('lftools.nexus.release_docker_hub.ProjectClass._docker_push', side_effect=self.mocked_docker_push)
        mocker.patch('lftools.nexus.release_docker_hub.ProjectClass._docker_cleanup', side_effect=self.mocked_docker_cleanup)

        project = ('onap', 'base/sdc-sanity')

        nexus_url = 'https://nexus3.onap.org:10002/v2/onap/base/sdc-sanity/tags/list'
        nexus_answer = '{"name":"onap/base_sdc-sanity","tags":["1.3.0","1.3.1","1.4.0","1.4.1","v1.0.0"]}'
        docker_url = 'https://registry.hub.docker.com/v1/repositories/onap/base-sdc-sanity/tags'
        docker_answer = """[{"layer": "", "name": "1.3.0"},
            {"layer": "", "name": "1.3.1"},
            {"layer": "", "name": "v1.0.0"}]
        """
        nexus_answer_valid_tags = ["1.3.0","1.3.1","1.4.0","1.4.1"]
        nexus_answer_invalid_tags = ["v1.0.0"]
        docker_answer_valid_tags = ["1.3.0","1.3.1"]
        docker_answer_invalid_tags = ["v1.0.0"]
        docker_missing_tags = ["1.4.0","1.4.1"]

        self.counter.pull = self.counter.tag = self.counter.push = self.counter.cleanup = 0

        responses.add(responses.GET, nexus_url, body=nexus_answer, status=200)
        responses.add(responses.GET, docker_url, body=docker_answer, status=200)

        rdh.initialize ('onap')
        test_proj = rdh.ProjectClass (project)

        assert test_proj.org_name == 'onap'
        assert test_proj.nexus_repo_name == 'base/sdc-sanity'
        assert test_proj.docker_repo_name == 'base-sdc-sanity'
        assert test_proj.calc_docker_project_name() == 'onap/base-sdc-sanity'

        assert len(test_proj.nexus_tags.valid) == len(nexus_answer_valid_tags)
        assert len(test_proj.docker_tags.valid) == len(docker_answer_valid_tags)
        assert len(test_proj.nexus_tags.invalid) == len(nexus_answer_invalid_tags)
        assert len(test_proj.docker_tags.invalid) == len(docker_answer_invalid_tags)

        for tag in docker_missing_tags:
            assert tag in test_proj.tags_2_copy.valid
        assert len(test_proj.tags_2_copy.valid) == len(docker_missing_tags)

        test_proj.docker_pull_tag_push()

        assert self.counter.pull == 2
        assert self.counter.tag == 2
        assert self.counter.push == 2
        assert self.counter.cleanup == 2

    def test_ProjectClass_1_missing(self, responses, mocker):
        """Test ProjectClass"""
        mocker.patch('lftools.nexus.release_docker_hub.ProjectClass._docker_pull', side_effect=self.mocked_docker_pull)
        mocker.patch('lftools.nexus.release_docker_hub.ProjectClass._docker_tag', side_effect=self.mocked_docker_tag)
        mocker.patch('lftools.nexus.release_docker_hub.ProjectClass._docker_push', side_effect=self.mocked_docker_push)
        mocker.patch('lftools.nexus.release_docker_hub.ProjectClass._docker_cleanup', side_effect=self.mocked_docker_cleanup)

        project = ('onap', 'base/sdc-sanity')

        nexus_url = 'https://nexus3.onap.org:10002/v2/onap/base/sdc-sanity/tags/list'
        nexus_answer = '{"name":"onap/base_sdc-sanity","tags":["1.3.0","1.3.1","1.4.0","v1.0.0"]}'
        docker_url = 'https://registry.hub.docker.com/v1/repositories/onap/base-sdc-sanity/tags'
        docker_answer = """[{"layer": "", "name": "1.3.0"},
            {"layer": "", "name": "1.3.1"},
            {"layer": "", "name": "v1.0.0"}]
        """
        nexus_answer_valid_tags = ["1.3.0","1.3.1","1.4.0"]
        nexus_answer_invalid_tags = ["v1.0.0"]
        docker_answer_valid_tags = ["1.3.0","1.3.1"]
        docker_answer_invalid_tags = ["v1.0.0"]
        docker_missing_tags = ["1.4.0"]

        self.counter.pull = self.counter.tag = self.counter.push = self.counter.cleanup = 0

        responses.add(responses.GET, nexus_url, body=nexus_answer, status=200)
        responses.add(responses.GET, docker_url, body=docker_answer, status=200)

        rdh.initialize ('onap')
        test_proj = rdh.ProjectClass (project)

        assert test_proj.org_name == 'onap'
        assert test_proj.nexus_repo_name == 'base/sdc-sanity'
        assert test_proj.docker_repo_name == 'base-sdc-sanity'
        assert test_proj.calc_docker_project_name() == 'onap/base-sdc-sanity'

        assert len(test_proj.nexus_tags.valid) == len(nexus_answer_valid_tags)
        assert len(test_proj.docker_tags.valid) == len(docker_answer_valid_tags)
        assert len(test_proj.nexus_tags.invalid) == len(nexus_answer_invalid_tags)
        assert len(test_proj.docker_tags.invalid) == len(docker_answer_invalid_tags)

        for tag in docker_missing_tags:
            assert tag in test_proj.tags_2_copy.valid
        assert len(test_proj.tags_2_copy.valid) == len(docker_missing_tags)

        test_proj.docker_pull_tag_push()

        assert self.counter.pull == 1
        assert self.counter.tag == 1
        assert self.counter.push == 1
        assert self.counter.cleanup == 1

    def test_ProjectClass_socket_timeout (self, responses, mocker):
        """Test ProjectClass"""
        mocker.patch('lftools.nexus.release_docker_hub.ProjectClass._docker_pull', side_effect=self.mocked_docker_pull)
        mocker.patch('lftools.nexus.release_docker_hub.ProjectClass._docker_tag', side_effect=self.mocked_docker_tag)
        mocker.patch('lftools.nexus.release_docker_hub.ProjectClass._docker_push', side_effect=self.mocked_docker_push)
        mocker.patch('lftools.nexus.release_docker_hub.ProjectClass._docker_cleanup', side_effect=self.mocked_docker_cleanup)

        project = ('onap', 'base/sdc-sanity')
        nexus_url = 'https://nexus3.onap.org:10002/v2/onap/base/sdc-sanity/tags/list'
        nexus_answer = '{"name":"onap/base_sdc-sanity","tags":["1.3.0","1.3.1","1.4.0","v1.0.0"]}'
        docker_url = 'https://registry.hub.docker.com/v1/repositories/onap/base-sdc-sanity/tags'
        docker_answer = """[{"layer": "", "name": "1.3.0"},
            {"layer": "", "name": "1.3.1"},
            {"layer": "", "name": "v1.0.0"}]
        """
        nexus_answer_valid_tags = ["1.3.0","1.3.1","1.4.0"]
        nexus_answer_invalid_tags = ["v1.0.0"]
        docker_answer_valid_tags = ["1.3.0","1.3.1"]
        docker_answer_invalid_tags = ["v1.0.0"]
        docker_missing_tags = ["1.4.0"]

        self.counter.pull = self.counter.tag = self.counter.push = self.counter.cleanup = 0

        responses.add(responses.GET, nexus_url, body=nexus_answer, status=200)
        responses.add(responses.GET, docker_url, body=docker_answer, status=200)

        rdh.initialize ('onap')
        test_proj = rdh.ProjectClass (project)

        assert test_proj.org_name == 'onap'
        assert test_proj.nexus_repo_name == 'base/sdc-sanity'
        assert test_proj.docker_repo_name == 'base-sdc-sanity'
        assert test_proj.calc_docker_project_name() == 'onap/base-sdc-sanity'

        assert len(test_proj.nexus_tags.valid) == len(nexus_answer_valid_tags)
        assert len(test_proj.docker_tags.valid) == len(docker_answer_valid_tags)
        assert len(test_proj.nexus_tags.invalid) == len(nexus_answer_invalid_tags)
        assert len(test_proj.docker_tags.invalid) == len(docker_answer_invalid_tags)

        for tag in docker_missing_tags:
            assert tag in test_proj.tags_2_copy.valid
        assert len(test_proj.tags_2_copy.valid) == len(docker_missing_tags)

        #Verify that 90 timeout's on any stage failes.
        self.nbr_exc.pull = 90
        with pytest.raises(requests.HTTPError) as excinfo:
            test_proj.docker_pull_tag_push()

        self.counter.pull = self.counter.tag = self.counter.push = self.counter.cleanup = 0
        self.nbr_exc.pull = 0
        self.nbr_exc.tag = 90
        with pytest.raises(requests.HTTPError) as excinfo:
            test_proj.docker_pull_tag_push()

        self.counter.pull = self.counter.tag = self.counter.push = self.counter.cleanup = 0
        self.nbr_exc.pull = self.nbr_exc.tag = 0
        self.nbr_exc.push = 90
        with pytest.raises(requests.HTTPError) as excinfo:
            test_proj.docker_pull_tag_push()

        self.counter.pull = self.counter.tag = self.counter.push = self.counter.cleanup = 0
        self.nbr_exc.pull = self.nbr_exc.tag = self.nbr_exc.push = 0
        self.nbr_exc.cleanup = 90
        with pytest.raises(requests.HTTPError) as excinfo:
            test_proj.docker_pull_tag_push()

        #Verify 89 timeouts and the 90 is ok per stage
        self.counter.pull = self.counter.tag = self.counter.push = self.counter.cleanup = 0
        self.nbr_exc.pull = self.nbr_exc.tag = self.nbr_exc.push = self.nbr_exc.cleanup = 89
        test_proj.docker_pull_tag_push()

        assert self.counter.pull == 90
        assert self.counter.tag == 90
        assert self.counter.push == 90
        assert self.counter.cleanup == 90
