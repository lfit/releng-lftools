# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2018 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Test rtd command."""

import json
import os

import pytest
import responses

import lftools.api.endpoints.readthedocs as client

creds = {"authtype": "token", "endpoint": "https://readthedocs.org/api/v3/", "token": "xyz"}
rtd = client.ReadTheDocs(creds=creds)

FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "fixtures",
)


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "rtd"),
)
@responses.activate
def test_project_list(datafiles):
    os.chdir(str(datafiles))
    json_file = open("project_list.json", "r")
    json_data = json.loads(json_file.read())
    responses.add(responses.GET, url="https://readthedocs.org/api/v3/projects/", json=json_data, status=200)
    assert "TestProject1" in rtd.project_list()


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "rtd"),
)
@responses.activate
def test_project_details(datafiles):
    os.chdir(str(datafiles))
    json_file = open("project_details.json", "r")
    json_data = json.loads(json_file.read())
    responses.add(
        responses.GET, url="https://readthedocs.org/api/v3/projects/TestProject1/", json=json_data, status=200
    )
    assert "slug" in rtd.project_details("TestProject1")


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "rtd"),
)
@responses.activate
def test_project_version_list(datafiles):
    os.chdir(str(datafiles))
    json_file = open("project_version_list.json", "r")
    json_data = json.loads(json_file.read())
    responses.add(
        responses.GET,
        url="https://readthedocs.org/api/v3/projects/TestProject1/versions/?active=True",  # noqa
        json=json_data,
        status=200,
        match_querystring=True,
    )
    assert "test-trigger6" in rtd.project_version_list("TestProject1")


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "rtd"),
)
@responses.activate
def test_project_version_details(datafiles):
    os.chdir(str(datafiles))
    json_file = open("project_version_details.json", "r")
    json_data = json.loads(json_file.read())
    responses.add(
        responses.GET,
        url="https://readthedocs.org/api/v3/projects/TestProject1/versions/latest/",  # noqa
        json=json_data,
        status=200,
    )
    assert "slug" in rtd.project_version_details("TestProject1", "latest")


@responses.activate
def test_project_version_update():
    data = {"active": True}
    responses.add(
        responses.PATCH,
        url="https://readthedocs.org/api/v3/projects/TestProject1/versions/latest/",  # noqa
        json=data,
        status=204,
    )
    assert rtd.project_version_update("TestProject1", "latest", "True")


@responses.activate
def test_project_create():
    data = {
        "name": "TestProject1",
        "repository": {"url": "https://repository_url", "type": "my_repo_type"},
        "homepage": "https://homepageurl",
        "programming_language": "py",
        "language": "en",
    }
    responses.add(responses.POST, url="https://readthedocs.org/api/v3/projects/", json=data, status=201)
    assert rtd.project_create(
        "TestProject1", "https://repository_url", "my_repo_type", "https://homepageurl", "py", "en"
    )


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "rtd"),
)
@responses.activate
def test_project_build_list(datafiles):
    os.chdir(str(datafiles))
    json_file = open("project_build_list.json", "r")
    json_data = json.loads(json_file.read())
    responses.add(
        responses.GET,
        url="https://readthedocs.org/api/v3/projects/testproject1/builds/?running=True",  # noqa
        json=json_data,
        status=200,
        match_querystring=True,
    )
    assert "success" in rtd.project_build_list("testproject1")


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "rtd"),
)
@responses.activate
def test_project_build_details(datafiles):
    os.chdir(str(datafiles))
    json_file = open("project_build_details.json", "r")
    json_data = json.loads(json_file.read())
    responses.add(
        responses.GET,
        url="https://readthedocs.org/api/v3/projects/testproject1/builds/9584913/",  # noqa
        json=json_data,
        status=200,
    )
    assert "id" in rtd.project_build_details("testproject1", 9584913)


@responses.activate
def test_project_build_trigger():
    data = {"project": "testproject1", "version": "latest"}
    responses.add(
        responses.POST,
        url="https://readthedocs.org/api/v3/projects/testproject1/versions/latest/builds/",  # noqa
        json=data,
        status=201,
    )
    assert rtd.project_build_trigger("testproject1", "latest")


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "rtd"),
)
@responses.activate
def test_subproject_list(datafiles):
    os.chdir(str(datafiles))
    json_file = open("subproject_list.json", "r")
    json_data = json.loads(json_file.read())
    responses.add(
        responses.GET,
        url="https://readthedocs.org/api/v3/projects/TestProject1/subprojects/?limit=999",  # noqa
        json=json_data,
        status=200,
        match_querystring=True,
    )
    assert "testproject2" in rtd.subproject_list("TestProject1")


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "rtd"),
)
@responses.activate
def test_subproject_details(datafiles):
    os.chdir(str(datafiles))
    json_file = open("subproject_details.json", "r")
    json_data = json.loads(json_file.read())
    responses.add(
        responses.GET,
        url="https://readthedocs.org/api/v3/projects/TestProject1/subprojects/testproject2/",  # NOQA
        json=json_data,
        status=200,
    )
    assert "child" in rtd.subproject_details("TestProject1", "testproject2")


@responses.activate
def test_subproject_create():
    responses.add(
        responses.POST, url="https://readthedocs.org/api/v3/projects/TestProject1/subprojects/", status=201  # NOQA
    )
    assert rtd.subproject_create("TestProject1", "testproject2")


def test_subproject_delete():
    assert "untested because responses doesn't have DELETE support"
