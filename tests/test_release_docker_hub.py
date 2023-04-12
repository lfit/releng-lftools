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

import pytest
import requests
import responses

import lftools.nexus.release_docker_hub as rdh

FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "fixtures",
)


def data_from_file(filename):
    """Return content from file"""
    with open(filename, "r") as f:
        return f.read()


def test_remove_http_from_url():
    """Test _remove_http_from_url."""
    test_url = [
        ["192.168.1.1", "192.168.1.1"],
        ["192.168.1.1:8081", "192.168.1.1:8081"],
        ["http://192.168.1.1:8081/nexus", "192.168.1.1:8081/nexus"],
        ["192.168.1.1:8081/nexus/", "192.168.1.1:8081/nexus/"],
        ["http://192.168.1.1:8081/nexus", "192.168.1.1:8081/nexus"],
        ["https://192.168.1.1:8081/nexus", "192.168.1.1:8081/nexus"],
        ["https://192.168.1.1:8081/nexus/", "192.168.1.1:8081/nexus/"],
        ["http://www.goodnexussite.org:8081", "www.goodnexussite.org:8081"],
    ]

    for url in test_url:
        assert rdh._remove_http_from_url(url[0]) == url[1]


def test_format_image_id():
    """Test _remove_http_from_url."""
    test_id = [
        ["b9e15a5d1e1a", "b9e15a5d1e1a"],
        ["sha256:b9e15a5d1e1a", "b9e15a5d1e1a"],
        ["sha256:3450464d68", "3450464d68"],
        ["192.168.1.1:8081/nexus/", "192.168.1.1:8081/nexus/"],
        [
            "sha256:3450464d68c9443dedc8bfe3272a23e6441c37f707c42d32fee0ebdbcd319d2c",
            "3450464d68c9443dedc8bfe3272a23e6441c37f707c42d32fee0ebdbcd319d2c",
        ],
    ]

    for id in test_id:
        assert rdh._format_image_id(id[0]) == id[1]


def test_nexus_tag_class(responses):
    """Test NexusTagClass"""
    org = "onap"
    repo = "sdc-helm-validator"
    repo_from_file = False
    url = "https://nexus3.onap.org:10002/v2/onap/sdc-helm-validator/tags/list"
    answer = (
        '{"name":"onap/sdc-helm-validator","tags":["latest","1.3.0","1.3.1","1.4.0","1.4.1","1.6.0","1.7.0","v1.0.0"]}'
    )
    answer_valid_tags = ["1.3.0", "1.3.1", "1.4.0", "1.4.1", "1.6.0", "1.7.0"]
    answer_invalid_tags = ["latest", "v1.0.0"]
    responses.add(responses.GET, url, body=answer, status=200)
    rdh.initialize(org)
    test_tags = rdh.NexusTagClass(org, repo, repo_from_file)
    for tag in answer_valid_tags:
        assert tag in test_tags.valid
    for tag in answer_invalid_tags:
        assert tag in test_tags.invalid
    assert len(test_tags.valid) == len(answer_valid_tags)
    assert len(test_tags.invalid) == len(answer_invalid_tags)


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "nexus"),
)
def test_docker_tag_class(responses, datafiles):
    """Test DockerTagClass"""
    org = "onap"
    repo = "sdc-helm-validator"
    repo_from_file = False
    url = "https://registry.hub.docker.com/v2/namespaces/onap/repositories/sdc-helm-validator/tags"
    answer = data_from_file(os.path.join(str(datafiles), "releasedockerhub_dockertags-sdc-helm-validator.json"))
    answer_valid_tags = ["1.3.0", "1.3.1", "1.4.0", "1.4.1", "1.6.0", "1.7.0"]
    answer_invalid_tags = ["latest", "v1.0.0"]
    responses.add(responses.GET, url, body=answer, status=200)
    rdh.initialize(org)
    test_tags = rdh.DockerTagClass(org, repo, repo_from_file)
    for tag in answer_valid_tags:
        assert tag in test_tags.valid
    for tag in answer_invalid_tags:
        assert tag in test_tags.invalid
    assert len(test_tags.valid) == len(answer_valid_tags)
    assert len(test_tags.invalid) == len(answer_invalid_tags)


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "nexus"),
)
def test_multiple_pages_4_dockertags(responses, datafiles):
    org = "onap"
    repo = "sdnc-aaf-image"
    repo_from_file = False
    url1 = "https://registry.hub.docker.com/v2/namespaces/onap/repositories/sdnc-aaf-image/tags"
    url2 = "https://registry.hub.docker.com/v2/namespaces/onap/repositories/sdnc-aaf-image/tags?page=2"
    url3 = "https://registry.hub.docker.com/v2/namespaces/onap/repositories/sdnc-aaf-image/tags?page=3"
    url4 = "https://registry.hub.docker.com/v2/namespaces/onap/repositories/sdnc-aaf-image/tags?page=4"
    url5 = "https://registry.hub.docker.com/v2/namespaces/onap/repositories/sdnc-aaf-image/tags?page=5"
    answer1 = data_from_file(os.path.join(str(datafiles), "releasedockerhub_dockertags-sdnc-aaf-image-page1.json"))
    answer2 = data_from_file(os.path.join(str(datafiles), "releasedockerhub_dockertags-sdnc-aaf-image-page2.json"))
    answer3 = data_from_file(os.path.join(str(datafiles), "releasedockerhub_dockertags-sdnc-aaf-image-page3.json"))
    answer4 = data_from_file(os.path.join(str(datafiles), "releasedockerhub_dockertags-sdnc-aaf-image-page4.json"))
    answer5 = data_from_file(os.path.join(str(datafiles), "releasedockerhub_dockertags-sdnc-aaf-image-page5.json"))
    answer_valid_tags = [
        "1.5.1",
        "1.5.2",
        "1.5.3",
        "1.5.4",
        "1.6.1",
        "1.6.2",
        "1.7.0",
        "1.7.3",
        "1.7.4",
        "1.7.5",
        "1.7.6",
        "1.7.7",
        "1.8.0",
        "1.8.1",
        "1.8.2",
        "1.8.3",
        "1.8.4",
        "2.0.0",
        "2.0.1",
        "2.0.2",
        "2.0.3",
        "2.0.4",
        "2.0.5",
        "2.0.6",
        "2.1.0",
        "2.1.1",
        "2.1.2",
        "2.1.3",
        "2.1.4",
        "2.1.5",
        "2.1.6",
        "2.2.0",
        "2.2.1",
        "2.2.2",
        "2.2.3",
        "2.2.4",
        "2.2.5",
        "2.3.0",
        "2.3.1",
        "2.3.2",
        "2.4.0",
        "2.4.1",
    ]
    answer_invalid_tags = []
    responses.add(responses.GET, url1, body=answer1, status=200)
    responses.add(responses.GET, url2, body=answer2, status=200)
    responses.add(responses.GET, url3, body=answer3, status=200)
    responses.add(responses.GET, url4, body=answer4, status=200)
    responses.add(responses.GET, url5, body=answer5, status=200)
    rdh.initialize(org)
    test_tags = rdh.DockerTagClass(org, repo, repo_from_file)
    for tag in answer_valid_tags:
        assert tag in test_tags.valid
    for tag in answer_invalid_tags:
        assert tag in test_tags.invalid
    assert len(test_tags.valid) == len(answer_valid_tags)
    assert len(test_tags.invalid) == len(answer_invalid_tags)


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "nexus"),
)
def test_docker_tag_err_429_class(responses, datafiles, mocker):
    """Test DockerTagClass"""
    mocker.patch("time.sleep", return_value=None)
    org = "onap"
    repo = "sdc-helm-validator"
    repo_from_file = False
    url = "https://registry.hub.docker.com/v2/namespaces/onap/repositories/sdc-helm-validator/tags"
    answer = data_from_file(os.path.join(str(datafiles), "releasedockerhub_dockertags-sdc-helm-validator.json"))
    answer_valid_tags = ["1.3.0", "1.3.1", "1.4.0", "1.4.1", "1.6.0", "1.7.0"]
    answer_invalid_tags = ["latest", "v1.0.0"]
    answer_429 = '{"detail": "Rate limit exceeded", "error": false}"'
    rdh.initialize(org)

    # Do 19 failed and next one should work
    for k in range(19):
        responses.add(responses.GET, url, body=answer_429, status=429)
    responses.add(responses.GET, url, body=answer, status=200)
    test_tags = rdh.DockerTagClass(org, repo, repo_from_file)
    assert len(test_tags.valid) == len(answer_valid_tags)
    assert len(test_tags.invalid) == len(answer_invalid_tags)

    # Do 20 failed, and all failes
    for k in range(20):
        responses.add(responses.GET, url, body=answer_429, status=429)
    with pytest.raises(requests.HTTPError):
        test_tags = rdh.DockerTagClass(org, repo, repo_from_file)


def test_tag_class_repository_exist():
    """Test TagClass"""
    org = "onap"
    repo = "sdc-helm-validator"
    repo_from_file = False
    rdh.initialize(org)
    tags = rdh.TagClass(org, repo, repo_from_file)
    assert tags.repository_exist


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "nexus"),
)
class TestTagsRegExpClass:
    """Test Tags and Regexp for Versions.

    This class contains all the test cases for Valid/Invalid tags and Version RegExp.
    """

    def test_tag_class_valid_tags(self):
        """Test TagClass"""
        org = "onap"
        repo = "sdc-helm-validator"
        repo_from_file = False
        test_tags = ["1.2.3", "1.22.333", "111.22.3", "10.11.12", "1.0.3"]
        rdh.initialize(org)
        tags = rdh.TagClass(org, repo, repo_from_file)
        for tag in test_tags:
            tags.add_tag(tag)
        assert len(tags.valid) == len(test_tags)
        assert len(tags.invalid) == 0

    def test_tag_class_invalid_tags(self):
        """Test TagClass"""
        org = "onap"
        repo = "sdc-helm-validator"

        repo_from_file = False
        test_tags = [
            "v1.2.3",
            "1.22",
            "111.22.3a",
            "10.11.12.3",
            "draft",
            "1.2.jan14",
            "1.2.3.4.5.6.7.8",
            "1",
            "latest",
            "v0.1.0",
            "1.1-20170906T011834",
            "2.0-20180221T152423",
            "1.3.0-20181121T1329",
            "1.1.2-SNAPSHOT-20181231T234559Z",
            "1.1.2-STAGING-20181231T234559Z",
        ]
        rdh.initialize(org)
        tags = rdh.TagClass(org, repo, repo_from_file)
        for tag in test_tags:
            tags.add_tag(tag)
        assert len(tags.invalid) == len(test_tags)
        assert len(tags.valid) == 0

    def test_tag_class_manual_version_regexp_str_valid_tags(self):
        """Test TagClass"""
        org = "onap"
        repo = "sdc-helm-validator"
        test_regexp = r"^v\d+.\d+.\d+$"
        repo_from_file = False
        test_tags = ["v1.2.3", "v1.22.333", "v111.22.3", "v10.11.12", "v1.0.3"]
        rdh.initialize(org, test_regexp)
        tags = rdh.TagClass(org, repo, repo_from_file)
        for tag in test_tags:
            tags.add_tag(tag)
        assert len(tags.valid) == len(test_tags)
        assert len(tags.invalid) == 0

    def test_tag_class_manual_version_regexp_str_invalid_tags(self):
        """Test TagClass"""
        org = "onap"
        repo = "sdc-helm-validator"
        test_regexp = r"v^\d+.\d+.\d+$"
        repo_from_file = False
        test_tags = [
            "1.2.3",
            "1.22",
            "111.22.3a",
            "10.11.12.3",
            "draft",
            "1.2.jan14",
            "1.2.3.4.5.6.7.8",
            "1",
            "latest",
            "0.1.0",
            "1.1-20170906T011834",
            "2.0-20180221T152423",
            "1.3.0-20181121T1329",
            "1.1.2-SNAPSHOT-20181231T234559Z",
            "1.1.2-STAGING-20181231T234559Z",
        ]
        rdh.initialize(org, test_regexp)
        tags = rdh.TagClass(org, repo, repo_from_file)
        for tag in test_tags:
            tags.add_tag(tag)
        assert len(tags.invalid) == len(test_tags)
        assert len(tags.valid) == 0

    def test_tag_class_manual_version_regexp_str_from_file_valid(self, datafiles):
        org = "onap"
        test_regexp_from_file = os.path.join(str(datafiles), "releasedockerhub_good_regexp")
        rdh.initialize(org, test_regexp_from_file)
        assert rdh.validate_regexp()
        assert rdh.VERSION_REGEXP == r"^\d+.\d+"

    def test_tag_class_manual_version_regexp_str_from_file_invalid(self, datafiles):
        org = "onap"
        test_regexp_from_file = os.path.join(str(datafiles), "releasedockerhub_bad_regexp")
        rdh.initialize(org, test_regexp_from_file)
        assert not rdh.validate_regexp()
        assert rdh.VERSION_REGEXP == "["


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "nexus"),
)
class TestProjectClass:
    """Test ProjectClass.

    This class contains all the test cases for the ProjectClass.
    We mock the helper functions _docker_pull, _docker_tag, _docker_push, and
    _docker_cleanup. This means we do not have to do anything with the actual
    docker api.
    """

    _test_image_long_id = "sha256:3450464d68c9443dedc8bfe3272a23e6441c37f707c42d32fee0ebdbcd319d2c"
    _test_image_short_id = "sha256:3450464d68"
    _expected_nexus_image_str = [
        "nexus3.onap.org:10002/onap/sdc-helm-validator:1.4.0",
        "nexus3.onap.org:10002/onap/sdc-helm-validator:1.4.1",
    ]

    class mock_image:
        id = ""
        short_id = ""

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

    def mocked_docker_pull(self, nexus_image_str, count, tag, retry_text="", progbar=False):
        """Mocking Pull an image from Nexus."""
        if nexus_image_str not in self._expected_nexus_image_str:
            raise ValueError("Wrong nexus project in pull")
        image = self.mock_image(self._test_image_long_id, self._test_image_short_id)
        self.counter.pull = self.counter.pull + 1
        if self.counter.pull > self.nbr_exc.pull:
            return image
        else:
            raise requests.exceptions.ConnectionError("Connection Error")

    def mocked_docker_tag(self, count, image, tag, retry_text="", progbar=False):
        """Mocking Tag the image with proper docker name and version."""
        if not image.id == self._test_image_long_id:
            raise ValueError("Wrong image id in remove")
        if tag not in ["1.4.0", "1.4.1"]:
            raise ValueError("Wrong tag in docker_tag")
        self.counter.tag = self.counter.tag + 1
        if self.counter.tag <= self.nbr_exc.tag:
            raise requests.exceptions.ConnectionError("Connection Error")

    def mocked_docker_push(self, count, image, tag, retry_text, progbar=False):
        """Mocking Tag the image with proper docker name and version."""
        if not image.id == self._test_image_long_id:
            raise ValueError("Wrong image id in remove")
        if tag not in ["1.4.0", "1.4.1"]:
            raise ValueError("Wrong tag in push")
        self.counter.push = self.counter.push + 1
        if self.counter.push <= self.nbr_exc.push:
            raise requests.exceptions.ConnectionError("Connection Error")

    def mocked_docker_cleanup(self, count, image, tag, retry_text="", progbar=False):
        """Mocking Tag the image with proper docker name and version."""
        if not image.id == self._test_image_long_id:
            raise ValueError("Wrong image id in remove")
        self.counter.cleanup = self.counter.cleanup + 1
        if self.counter.cleanup <= self.nbr_exc.cleanup:
            raise requests.exceptions.ConnectionError("Connection Error")

    def test_ProjectClass_2_missing(self, responses, datafiles, mocker):
        """Test ProjectClass"""
        mocker.patch("lftools.nexus.release_docker_hub.ProjectClass._docker_pull", side_effect=self.mocked_docker_pull)
        mocker.patch("lftools.nexus.release_docker_hub.ProjectClass._docker_tag", side_effect=self.mocked_docker_tag)
        mocker.patch("lftools.nexus.release_docker_hub.ProjectClass._docker_push", side_effect=self.mocked_docker_push)
        mocker.patch(
            "lftools.nexus.release_docker_hub.ProjectClass._docker_cleanup", side_effect=self.mocked_docker_cleanup
        )

        project = ["onap", "sdc-helm-validator", ""]

        nexus_url = "https://nexus3.onap.org:10002/v2/onap/sdc-helm-validator/tags/list"
        nexus_answer = '{"name":"onap/sdc-helm-validator","tags":["v1.0.0","1.3.0", "1.3.1", "1.4.0", "1.4.1","1.6.0", "1.7.0","latest"]}'  # noqa
        nexus_answer_valid_tags = ["1.3.0", "1.3.1", "1.4.0", "1.4.1", "1.6.0", "1.7.0"]
        nexus_answer_invalid_tags = ["v1.0.0", "latest"]
        docker_url = "https://registry.hub.docker.com/v2/namespaces/onap/repositories/sdc-helm-validator/tags"
        docker_answer = data_from_file(
            os.path.join(str(datafiles), "releasedockerhub_dockertags-sdc-helm-validator-missing2.json")
        )
        docker_answer_valid_tags = ["1.3.0", "1.3.1", "1.6.0", "1.7.0"]
        docker_answer_invalid_tags = ["latest", "v1.0.0"]
        docker_missing_tags = ["1.4.0", "1.4.1"]

        self.counter.pull = self.counter.tag = self.counter.push = self.counter.cleanup = 0

        responses.add(responses.GET, nexus_url, body=nexus_answer, status=200)
        responses.add(responses.GET, docker_url, body=docker_answer, status=200)

        rdh.initialize("onap")
        test_proj = rdh.ProjectClass(project)

        assert test_proj.org_name == "onap"
        assert test_proj.nexus_repo_name == "sdc-helm-validator"
        assert test_proj.docker_repo_name == "sdc-helm-validator"
        assert test_proj.calc_docker_project_name() == "onap/sdc-helm-validator"

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

    def test_ProjectClass_1_missing(self, responses, datafiles, mocker):
        """Test ProjectClass"""
        mocker.patch("lftools.nexus.release_docker_hub.ProjectClass._docker_pull", side_effect=self.mocked_docker_pull)
        mocker.patch("lftools.nexus.release_docker_hub.ProjectClass._docker_tag", side_effect=self.mocked_docker_tag)
        mocker.patch("lftools.nexus.release_docker_hub.ProjectClass._docker_push", side_effect=self.mocked_docker_push)
        mocker.patch(
            "lftools.nexus.release_docker_hub.ProjectClass._docker_cleanup", side_effect=self.mocked_docker_cleanup
        )

        project = ["onap", "sdc-helm-validator", ""]

        nexus_url = "https://nexus3.onap.org:10002/v2/onap/sdc-helm-validator/tags/list"
        nexus_answer = '{"name":"onap/sdc-helm-validator","tags":["v1.0.0","1.3.0", "1.3.1", "1.4.0", "1.4.1","1.6.0", "1.7.0","latest"]}'  # noqa
        nexus_answer_valid_tags = ["1.3.0", "1.3.1", "1.4.0", "1.4.1", "1.6.0", "1.7.0"]
        nexus_answer_invalid_tags = ["v1.0.0", "latest"]
        docker_url = "https://registry.hub.docker.com/v2/namespaces/onap/repositories/sdc-helm-validator/tags"
        docker_answer = data_from_file(
            os.path.join(str(datafiles), "releasedockerhub_dockertags-sdc-helm-validator-missing1.json")
        )
        docker_answer_valid_tags = ["1.3.0", "1.3.1", "1.4.1", "1.6.0", "1.7.0"]
        docker_answer_invalid_tags = ["latest", "v1.0.0"]
        docker_missing_tags = [
            "1.4.0",
        ]

        self.counter.pull = self.counter.tag = self.counter.push = self.counter.cleanup = 0

        responses.add(responses.GET, nexus_url, body=nexus_answer, status=200)
        responses.add(responses.GET, docker_url, body=docker_answer, status=200)

        rdh.initialize("onap")
        test_proj = rdh.ProjectClass(project)

        assert test_proj.org_name == "onap"
        assert test_proj.nexus_repo_name == "sdc-helm-validator"
        assert test_proj.docker_repo_name == "sdc-helm-validator"
        assert test_proj.calc_docker_project_name() == "onap/sdc-helm-validator"

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

    def test_ProjectClass_socket_timeout(self, responses, datafiles, mocker):
        """Test ProjectClass"""
        mocker.patch("lftools.nexus.release_docker_hub.ProjectClass._docker_pull", side_effect=self.mocked_docker_pull)
        mocker.patch("lftools.nexus.release_docker_hub.ProjectClass._docker_tag", side_effect=self.mocked_docker_tag)
        mocker.patch("lftools.nexus.release_docker_hub.ProjectClass._docker_push", side_effect=self.mocked_docker_push)
        mocker.patch(
            "lftools.nexus.release_docker_hub.ProjectClass._docker_cleanup", side_effect=self.mocked_docker_cleanup
        )

        project = ["onap", "sdc-helm-validator", ""]
        nexus_url = "https://nexus3.onap.org:10002/v2/onap/sdc-helm-validator/tags/list"
        nexus_answer = '{"name":"onap/sdc-helm-validator","tags":["v1.0.0","1.3.0", "1.3.1", "1.4.0", "1.4.1","1.6.0", "1.7.0","latest"]}'  # noqa
        nexus_answer_valid_tags = ["1.3.0", "1.3.1", "1.4.0", "1.4.1", "1.6.0", "1.7.0"]
        nexus_answer_invalid_tags = ["v1.0.0", "latest"]
        docker_url = "https://registry.hub.docker.com/v2/namespaces/onap/repositories/sdc-helm-validator/tags"
        docker_answer = data_from_file(
            os.path.join(str(datafiles), "releasedockerhub_dockertags-sdc-helm-validator-missing1.json")
        )
        docker_answer_valid_tags = ["1.3.0", "1.3.1", "1.4.1", "1.6.0", "1.7.0"]
        docker_answer_invalid_tags = ["latest", "v1.0.0"]
        docker_missing_tags = [
            "1.4.0",
        ]

        self.counter.pull = self.counter.tag = self.counter.push = self.counter.cleanup = 0

        responses.add(responses.GET, nexus_url, body=nexus_answer, status=200)
        responses.add(responses.GET, docker_url, body=docker_answer, status=200)

        rdh.initialize("onap")
        test_proj = rdh.ProjectClass(project)

        assert test_proj.org_name == "onap"
        assert test_proj.nexus_repo_name == "sdc-helm-validator"
        assert test_proj.docker_repo_name == "sdc-helm-validator"
        assert test_proj.calc_docker_project_name() == "onap/sdc-helm-validator"

        assert len(test_proj.nexus_tags.valid) == len(nexus_answer_valid_tags)
        assert len(test_proj.docker_tags.valid) == len(docker_answer_valid_tags)
        assert len(test_proj.nexus_tags.invalid) == len(nexus_answer_invalid_tags)
        assert len(test_proj.docker_tags.invalid) == len(docker_answer_invalid_tags)

        for tag in docker_missing_tags:
            assert tag in test_proj.tags_2_copy.valid
        assert len(test_proj.tags_2_copy.valid) == len(docker_missing_tags)

        # Verify that 90 timeout's on any stage failes.
        self.nbr_exc.pull = 90
        with pytest.raises(requests.HTTPError):
            test_proj.docker_pull_tag_push()

        self.counter.pull = self.counter.tag = self.counter.push = self.counter.cleanup = 0
        self.nbr_exc.pull = 0
        self.nbr_exc.tag = 90
        with pytest.raises(requests.HTTPError):
            test_proj.docker_pull_tag_push()

        self.counter.pull = self.counter.tag = self.counter.push = self.counter.cleanup = 0
        self.nbr_exc.pull = self.nbr_exc.tag = 0
        self.nbr_exc.push = 90
        with pytest.raises(requests.HTTPError):
            test_proj.docker_pull_tag_push()

        self.counter.pull = self.counter.tag = self.counter.push = self.counter.cleanup = 0
        self.nbr_exc.pull = self.nbr_exc.tag = self.nbr_exc.push = 0
        self.nbr_exc.cleanup = 90
        with pytest.raises(requests.HTTPError):
            test_proj.docker_pull_tag_push()

        # Verify 89 timeouts and the 90 is ok per stage
        self.counter.pull = self.counter.tag = self.counter.push = self.counter.cleanup = 0
        self.nbr_exc.pull = self.nbr_exc.tag = self.nbr_exc.push = self.nbr_exc.cleanup = 89
        test_proj.docker_pull_tag_push()

        assert self.counter.pull == 90
        assert self.counter.tag == 90
        assert self.counter.push == 90
        assert self.counter.cleanup == 90


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "nexus"),
)
class TestFetchNexus3Catalog:
    url = "https://nexus3.onap.org:10002/v2/_catalog"
    answer = """
         {"repositories":["dcae_dmaapbc","onap/aaf/aaf-base-openssl_1.1.0","onap/aaf/aaf-base-xenial","onap/aaf/aaf_agent","onap/aaf/aaf_cass","onap/aaf/aaf_cm","onap/aaf/aaf_config","onap/aaf/aaf_core","onap/aaf/aaf_fs","onap/aaf/aaf_gui","onap/aaf/aaf_hello","onap/aaf/aaf_locate","onap/aaf/aaf_oauth","onap/aaf/aaf_service","onap/aaf/abrmd","onap/aaf/distcenter","onap/aaf/sms","onap/aaf/smsquorumclient","onap/aaf/testcaservice","onap/aai-cacher","onap/aai-graphadmin","onap/aai-resources","onap/aai-traversal","onap/aai/esr-gui","onap/aai/esr-server","onap/admportal-sdnc-image","onap/appc-cdt-image","onap/appc-image","onap/babel","onap/base_sdc-cassandra","onap/base_sdc-cqlsh","onap/base_sdc-elasticsearch","onap/base_sdc-jetty","onap/base_sdc-kibana","onap/base_sdc-python","onap/base_sdc-sanity","onap/base_sdc-vnc","onap/ccsdk-ansible-server-image","onap/ccsdk-apps-ms-neng","onap/ccsdk-controllerblueprints","onap/ccsdk-dgbuilder-image","onap/ccsdk-odl-image","onap/ccsdk-odl-oxygen-image","onap/ccsdk-odlsli-image","onap/ccsdk-ubuntu-image","onap/chameleon","onap/champ","onap/clamp","onap/clamp-dashboard-kibana","onap/clamp-dashboard-logstash","onap/cli","onap/data-router","onap/dcae-be","onap/dcae-ci-tests","onap/dcae-dt","onap/dcae-fe","onap/dcae-tools","onap/dcae-tosca-app","onap/dmaap/buscontroller","onap/dmaap/datarouter-node","onap/dmaap/datarouter-prov","onap/dmaap/datarouter-subscriber","onap/dmaap/dmaap-mr","onap/dmaap/kafka01101","onap/externalapi/nbi","onap/gallifrey","onap/gizmo","onap/holmes/engine-management","onap/holmes/rule-management","onap/model-loader","onap/msb/msb_apigateway","onap/msb/msb_base","onap/msb/msb_discovery","onap/multicloud/azure","onap/multicloud/framework","onap/multicloud/openstack-newton","onap/multicloud/openstack-ocata","onap/multicloud/openstack-pike","onap/multicloud/openstack-windriver","onap/multicloud/openstack/openstack-ocata","onap/multicloud/vio","onap/multicloud/vio-vesagent","onap/music/cassandra_3_11","onap/music/cassandra_job","onap/music/cassandra_music","onap/music/music","onap/music/prom","onap/network-discovery","onap/oom/kube2msb","onap/optf-cmso-dbinit","onap/optf-cmso-service","onap/optf-has","onap/optf-osdf","onap/org.onap.dcaegen2.collectors.datafile.datafile-app-server","onap/org.onap.dcaegen2.collectors.hv-ves.hv-collector-main","onap/org.onap.dcaegen2.collectors.snmptrap","onap/org.onap.dcaegen2.collectors.ves.vescollector","onap/org.onap.dcaegen2.deployments.bootstrap","onap/org.onap.dcaegen2.deployments.cm-container","onap/org.onap.dcaegen2.deployments.healthcheck-container","onap/org.onap.dcaegen2.deployments.k8s-bootstrap-container","onap/org.onap.dcaegen2.deployments.redis-cluster-container","onap/org.onap.dcaegen2.deployments.tca-cdap-container","onap/org.onap.dcaegen2.deployments.tls-init-container","onap/org.onap.dcaegen2.platform.cdapbroker","onap/org.onap.dcaegen2.platform.configbinding","onap/org.onap.dcaegen2.platform.configbinding.app-app","onap/org.onap.dcaegen2.platform.deployment-handler","onap/org.onap.dcaegen2.platform.inventory-api","onap/org.onap.dcaegen2.platform.policy-handler","onap/org.onap.dcaegen2.platform.servicechange-handler","onap/org.onap.dcaegen2.services.prh.prh-app-server","onap/policy-apex-pdp","onap/policy-distribution","onap/policy-drools","onap/policy-pe","onap/policy/policy-db","onap/policy/policy-drools","onap/policy/policy-nexus","onap/policy/policy-pe","onap/pomba-aai-context-builder","onap/pomba-context-aggregator","onap/pomba-network-discovery-context-builder","onap/pomba-sdc-context-builder","onap/portal-app","onap/portal-apps","onap/portal-db","onap/portal-sdk","onap/portal-wms","onap/refrepo/postgres","onap/sdc-api-tests","onap/sdc-backend","onap/sdc-backend-init","onap/sdc-cassandra","onap/sdc-cassandra-init","onap/sdc-elasticsearch","onap/sdc-frontend","onap/sdc-init-elasticsearch","onap/sdc-kibana","onap/sdc-onboard-backend","onap/sdc-onboard-cassandra-init","onap/sdc-simulator","onap/sdc-ui-tests","onap/sdc/sdc-workflow-designer","onap/sdnc-ansible-server-image","onap/sdnc-dmaap-listener-image","onap/sdnc-image","onap/sdnc-ueb-listener-image","onap/search-data-service","onap/service-decomposition","onap/sniroemulator","onap/so/api-handler-infra","onap/so/asdc-controller","onap/so/base-image","onap/so/bpmn-infra","onap/so/catalog-db-adapter","onap/so/openstack-adapter","onap/so/request-db-adapter","onap/so/sdc-controller","onap/so/sdnc-adapter","onap/so/so-monitoring","onap/so/vfc-adapter","onap/sparky-be","onap/spike","onap/testsuite","onap/usecase-ui","onap/usecase-ui-server","onap/usecase-ui/usecase-ui-server","onap/validation","onap/vfc/catalog","onap/vfc/db","onap/vfc/emsdriver","onap/vfc/gvnfmdriver","onap/vfc/jujudriver","onap/vfc/multivimproxy","onap/vfc/nfvo/svnfm/huawei","onap/vfc/nfvo/svnfm/nokia","onap/vfc/nfvo/svnfm/nokiav2","onap/vfc/nslcm","onap/vfc/resmanagement","onap/vfc/vnflcm","onap/vfc/vnfmgr","onap/vfc/vnfres","onap/vfc/wfengine-activiti","onap/vfc/wfengine-mgrservice","onap/vfc/ztesdncdriver","onap/vfc/ztevmanagerdriver","onap/vfc/ztevnfmdriver","onap/vid","onap/vnfsdk/ice","onap/vnfsdk/refrepo","onap/vnfsdk/refrepo/postgres","onap/vnfsdk/vnftest","onap/vvp/cms","onap/vvp/engagementmgr","onap/vvp/gitlab","onap/vvp/image-scanner","onap/vvp/jenkins","onap/vvp/portal","onap/vvp/postgresql","onap/vvp/test-engine","onap/workflow-backend","onap/workflow-frontend","onap/workflow-init","openecomp/aai-cacher","openecomp/aai-resources","openecomp/aai-traversal","openecomp/appc-image","openecomp/base_sdc-backend","openecomp/base_sdc-cassandra","openecomp/base_sdc-elasticsearch","openecomp/base_sdc-frontend","openecomp/base_sdc-kibana","openecomp/base_sdc-sanity","openecomp/jacoco","openecomp/mso","openecomp/mso-arquillian","openecomp/portalapps","openecomp/portaldb","openecomp/sdc-backend","openecomp/sdc-cassandra","openecomp/sdc-elasticsearch","openecomp/sdc-frontend","openecomp/sdc-kibana","openecomp/sdc-sanity","openecomp/ubuntu-update","openecomp/vid","openecomp/wildfly"]}
     """

    def test_get_all_onap(self):
        rdh.NexusCatalog = []
        rdh.initialize("onap")
        responses.add(responses.GET, self.url, body=self.answer, status=200)
        rdh.get_nexus3_catalog("onap")
        assert len(rdh.NexusCatalog) == 203

    def test_get_all_onap_and_filter_1(self):
        rdh.NexusCatalog = []
        rdh.initialize("onap")
        responses.add(responses.GET, self.url, body=self.answer, status=200)
        rdh.get_nexus3_catalog("onap", "spike")
        assert len(rdh.NexusCatalog) == 1
        assert rdh.NexusCatalog[0][0] == "onap"
        assert rdh.NexusCatalog[0][1] == "spike"

    def test_get_all_onap_and_filter_18(self):
        rdh.NexusCatalog = []
        rdh.initialize("onap")
        responses.add(responses.GET, self.url, body=self.answer, status=200)
        rdh.get_nexus3_catalog("onap", "aaf")
        assert len(rdh.NexusCatalog) == 18

    def test_get_all_onap_and_specify_1_repo_1(self):
        rdh.NexusCatalog = []
        rdh.initialize("onap")
        responses.add(responses.GET, self.url, body=self.answer, status=200)
        rdh.get_nexus3_catalog("onap", "clamp", True)
        assert len(rdh.NexusCatalog) == 1
        assert rdh.NexusCatalog[0][1] == "clamp"

    def test_get_all_onap_and_specify_1_repo_2(self):
        rdh.NexusCatalog = []
        rdh.initialize("onap")
        responses.add(responses.GET, self.url, body=self.answer, status=200)
        rdh.get_nexus3_catalog("onap", "clamp-dashboard-logstash", True)
        assert len(rdh.NexusCatalog) == 1
        assert rdh.NexusCatalog[0][1] == "clamp-dashboard-logstash"

    def test_get_all_onap_and_specify_repo_file(self, datafiles):
        repo_names_file = os.path.join(str(datafiles), "releasedockerhub_reponamelist1.txt")
        rdh.NexusCatalog = []
        rdh.initialize("onap")
        responses.add(responses.GET, self.url, body=self.answer, status=200)
        rdh.get_nexus3_catalog("onap", repo_names_file, False, True)
        assert len(rdh.NexusCatalog) == 4
        assert rdh.NexusCatalog[0][1] == "dcae_dmaapbc"
        assert rdh.NexusCatalog[1][1] == "onap/aaf/aaf_core"
        assert rdh.NexusCatalog[2][1] == "onap/clamp"
        assert rdh.NexusCatalog[3][1] == "onap/vfc/nfvo/svnfm/nokiav2"


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "nexus"),
)
class TestFetchAllTagsAndUpdate:
    _test_image_long_id = "sha256:3450464d68c9443dedc8bfe3272a23e6441c37f707c42d32fee0ebdbcd319d2c"
    _test_image_short_id = "sha256:3450464d68"
    _expected_nexus_image_str = [
        "nexus3.onap.org:10002/onap/sdc-helm-validator:1.4.0",
        "nexus3.onap.org:10002/onap/gizmo2:1.3.1",
        "nexus3.onap.org:10002/onap/gizmo2:1.3.2",
    ]

    class mock_image:
        id = ""
        short_id = ""

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

    def mocked_docker_pull(self, nexus_image_str, count, tag, retry_text="", progbar=False):
        """Mocking Pull an image from Nexus."""
        if nexus_image_str not in self._expected_nexus_image_str:
            print("IMAGESTR {}".format(nexus_image_str))
            raise ValueError("Wrong nexus project in pull")
        image = self.mock_image(self._test_image_long_id, self._test_image_short_id)
        self.counter.pull = self.counter.pull + 1
        if self.counter.pull > self.nbr_exc.pull:
            return image
        else:
            raise requests.exceptions.ConnectionError("Connection Error")

    def mocked_docker_tag(self, count, image, tag, retry_text="", progbar=False):
        """Mocking Tag the image with proper docker name and version."""
        if not image.id == self._test_image_long_id:
            raise ValueError("Wrong image id in remove")
        if tag not in ["1.4.0", "1.3.1", "1.3.2"]:
            raise ValueError("Wrong tag in docker_tag")
        self.counter.tag = self.counter.tag + 1
        if self.counter.tag <= self.nbr_exc.tag:
            raise requests.exceptions.ConnectionError("Connection Error")

    def mocked_docker_push(self, count, image, tag, retry_text, progbar=False):
        """Mocking Tag the image with proper docker name and version."""
        if not image.id == self._test_image_long_id:
            raise ValueError("Wrong image id in remove")
        if tag not in ["1.4.0", "1.3.1", "1.3.2"]:
            raise ValueError("Wrong tag in push")
        self.counter.push = self.counter.push + 1
        if self.counter.push <= self.nbr_exc.push:
            raise requests.exceptions.ConnectionError("Connection Error")

    def mocked_docker_cleanup(self, count, image, tag, retry_text="", progbar=False):
        """Mocking Tag the image with proper docker name and version."""
        if not image.id == self._test_image_long_id:
            raise ValueError("Wrong image id in remove")
        self.counter.cleanup = self.counter.cleanup + 1
        if self.counter.cleanup <= self.nbr_exc.cleanup:
            raise requests.exceptions.ConnectionError("Connection Error")

    def initiate_test_fetch(self, responses, datafiles, mocker, repo=""):
        mocker.patch("lftools.nexus.release_docker_hub.ProjectClass._docker_pull", side_effect=self.mocked_docker_pull)
        mocker.patch("lftools.nexus.release_docker_hub.ProjectClass._docker_tag", side_effect=self.mocked_docker_tag)
        mocker.patch("lftools.nexus.release_docker_hub.ProjectClass._docker_push", side_effect=self.mocked_docker_push)
        mocker.patch(
            "lftools.nexus.release_docker_hub.ProjectClass._docker_cleanup", side_effect=self.mocked_docker_cleanup
        )
        catalog_url = "https://nexus3.onap.org:10002/v2/_catalog"
        catalog_answer = '{"repositories":["onap/sdc-helm-validator","onap/gizmo","onap/gizmo2"]}'

        # Missing one tag in docker
        nexus_url1 = "https://nexus3.onap.org:10002/v2/onap/sdc-helm-validator/tags/list"
        nexus_answer1 = '{"name":"onap/sdc-helm-validator","tags":["v1.0.0","1.3.0", "1.3.1", "1.4.0", "1.4.1","1.6.0", "1.7.0","latest"]}'  # noqa
        docker_url1 = "https://registry.hub.docker.com/v2/namespaces/onap/repositories/sdc-helm-validator/tags"
        docker_answer1 = data_from_file(
            os.path.join(str(datafiles), "releasedockerhub_dockertags-sdc-helm-validator-missing1.json")
        )

        # No missing tags
        nexus_url2 = "https://nexus3.onap.org:10002/v2/onap/gizmo/tags/list"
        nexus_answer2 = '{"name":"onap/gizmo","tags":["1.2.0","1.2.1","1.3.0","1.3.1","1.3.2","1.4.0","1.5.2"]}'
        docker_url2 = "https://registry.hub.docker.com/v2/namespaces/onap/repositories/gizmo/tags"
        docker_answer2 = data_from_file(os.path.join(str(datafiles), "releasedockerhub_dockertags-gizmo.json"))

        # Missing two tags in docker
        nexus_url3 = "https://nexus3.onap.org:10002/v2/onap/gizmo2/tags/list"
        nexus_answer3 = '{"name":"onap/gizmo2","tags":["1.2.1","1.3.1","1.3.2"]}'
        docker_url3 = "https://registry.hub.docker.com/v2/namespaces/onap/repositories/gizmo2/tags"
        docker_answer3 = data_from_file(os.path.join(str(datafiles), "releasedockerhub_dockertags-gizmo2.json"))

        responses.add(responses.GET, catalog_url, body=catalog_answer, status=200)

        rdh.NexusCatalog = []
        rdh.projects = []

        responses.add(responses.GET, nexus_url1, body=nexus_answer1, status=200)
        responses.add(responses.GET, docker_url1, body=docker_answer1, status=200)
        if len(repo) == 0:
            responses.add(responses.GET, nexus_url2, body=nexus_answer2, status=200)
            responses.add(responses.GET, docker_url2, body=docker_answer2, status=200)
            responses.add(responses.GET, nexus_url3, body=nexus_answer3, status=200)
            responses.add(responses.GET, docker_url3, body=docker_answer3, status=200)

        self.counter.pull = self.counter.tag = self.counter.push = self.counter.cleanup = 0

    def initiate_bogus_org_test_fetch(self, responses, org):
        url = "https://nexus3.{}.org:10002/v2/_catalog".format(org)
        exception = requests.HTTPError(
            "Issues with URL: {} - <class 'requests.exceptions.ConnectionError'>".format(url)
        )
        responses.add(responses.GET, url, body=exception)
        rdh.NexusCatalog = []
        rdh.projects = []
        self.counter.pull = self.counter.tag = self.counter.push = self.counter.cleanup = 0

    def test_fetch_all_tags(self, responses, datafiles, mocker):
        self.initiate_test_fetch(responses, datafiles, mocker)
        rdh.initialize("onap")
        rdh.get_nexus3_catalog("onap")
        rdh.fetch_all_tags()
        assert len(rdh.NexusCatalog) == 3
        assert len(rdh.projects) == 3
        assert len(rdh.projects[0].tags_2_copy.valid) == 0
        assert len(rdh.projects[1].tags_2_copy.valid) == 2
        assert len(rdh.projects[2].tags_2_copy.valid) == 1

        assert rdh.projects[1].tags_2_copy.valid[0] == "1.3.1"
        assert rdh.projects[1].tags_2_copy.valid[1] == "1.3.2"
        assert rdh.projects[2].tags_2_copy.valid[0] == "1.4.0"

    def test_fetch_from_bogus_orgs(self, responses, mocker):
        self.initiate_bogus_org_test_fetch(responses, "bogus_org321")
        rdh.initialize("bogus_org321")
        rdh.get_nexus3_catalog("bogus_org321")
        assert len(rdh.NexusCatalog) == 0
        assert len(rdh.projects) == 0

    def test_copy(self, responses, datafiles, mocker):
        self.initiate_test_fetch(responses, datafiles, mocker)
        rdh.initialize("onap")
        rdh.get_nexus3_catalog("onap")
        rdh.fetch_all_tags()
        rdh.copy_from_nexus_to_docker()
        assert self.counter.pull == 3
        assert self.counter.tag == 3
        assert self.counter.push == 3
        assert self.counter.cleanup == 3

    def test_start_no_copy(self, responses, datafiles, mocker):
        self.initiate_test_fetch(responses, datafiles, mocker)
        rdh.start_point("onap", "", False, False)
        assert self.counter.pull == 0
        assert self.counter.tag == 0
        assert self.counter.push == 0
        assert self.counter.cleanup == 0

    def test_start_copy(self, responses, datafiles, mocker):
        self.initiate_test_fetch(responses, datafiles, mocker)
        rdh.start_point("onap", "", False, False, False, True)
        assert len(rdh.NexusCatalog) == 3
        assert len(rdh.projects) == 3
        assert len(rdh.projects[0].tags_2_copy.valid) == 0
        assert len(rdh.projects[1].tags_2_copy.valid) == 2
        assert len(rdh.projects[2].tags_2_copy.valid) == 1
        assert rdh.projects[1].tags_2_copy.valid[0] == "1.3.1"
        assert rdh.projects[1].tags_2_copy.valid[1] == "1.3.2"
        assert rdh.projects[2].tags_2_copy.valid[0] == "1.4.0"
        assert self.counter.pull == 3
        assert self.counter.tag == 3
        assert self.counter.push == 3
        assert self.counter.cleanup == 3

    def test_start_copy_repo(self, responses, datafiles, mocker):
        self.initiate_test_fetch(responses, datafiles, mocker, "sanity")
        rdh.start_point("onap", "validator", False, False, False, True)
        assert len(rdh.NexusCatalog) == 1
        assert len(rdh.projects) == 1
        assert len(rdh.projects[0].tags_2_copy.valid) == 1
        assert rdh.projects[0].tags_2_copy.valid[0] == "1.4.0"
        assert self.counter.pull == 1
        assert self.counter.tag == 1
        assert self.counter.push == 1
        assert self.counter.cleanup == 1

    def test_start_bogus_orgs(self, responses):
        self.initiate_bogus_org_test_fetch(responses, "bogus_org321")
        rdh.start_point("bogus_org321")
        assert len(rdh.NexusCatalog) == 0
        assert len(rdh.projects) == 0


def test_calculate_docker_project_name():
    project = ["onap", "this/is/a-test_project", ""]
    rdh.initialize("onap")
    test_proj = rdh.ProjectClass(project)

    assert test_proj.org_name == "onap"
    assert test_proj.nexus_repo_name == "this/is/a-test_project"
    assert test_proj.docker_repo_name == "this-is-a-test_project"
    assert test_proj.calc_docker_project_name() == "onap/this-is-a-test_project"
