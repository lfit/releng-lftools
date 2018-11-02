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
from requests.exceptions import ConnectionError, MissingSchema, InvalidURL

from lftools import cli
import lftools.deploy as deploy_sys
import mock
import requests

FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'fixtures',
    )


def test_log_and_exit():
    """Test exit."""
    with pytest.raises(SystemExit) as excinfo:
        deploy_sys._log_error_and_exit("testmsg")
    assert excinfo.type == SystemExit


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, 'deploy'),
    )
def test_copy_archive_dir(cli_runner, datafiles):
    """Test copy_archives() command to ensure archives dir is copied."""
    os.chdir(str(datafiles))
    workspace_dir = os.path.join(str(datafiles), 'workspace')
    stage_dir = str(datafiles.mkdir("stage_archive"))

    os.chdir(stage_dir)
    result = cli_runner.invoke(
        cli.cli,
        ['--debug', 'deploy', 'copy-archives', workspace_dir],
        obj={})
    assert result.exit_code == 0

    assert os.path.exists(os.path.join(stage_dir, 'test.log'))

@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, 'deploy'),
    )
def test_copy_archive_pattern(cli_runner, datafiles):
    """Test copy_archives() command to ensure glob patterns are copied."""
    os.chdir(str(datafiles))
    workspace_dir = os.path.join(str(datafiles), 'workspace')
    stage_dir = str(datafiles.mkdir("stage_archive"))

    os.chdir(stage_dir)
    result = cli_runner.invoke(
        cli.cli,
        ['--debug', 'deploy', 'copy-archives', workspace_dir, '**/*.txt'],
        obj={})
    assert result.exit_code == 0

    assert os.path.exists(os.path.join(stage_dir, 'test.log'))
    assert os.path.exists(os.path.join(stage_dir, 'abc.txt'))
    assert not os.path.exists(os.path.join(stage_dir, 'dependencies.log'))
    assert os.path.exists(os.path.join(
        stage_dir, 'aaa', 'aaa-cert', 'target', 'surefire-reports',
        'org.opendaylight.aaa.cert.test.AaaCertMdsalProviderTest-output.txt'))

def mocked_log_error(msg1=None, msg2=None):
    """Mock local_log_error_and_exit function.
    This function is modified to simply raise an Exception.
    The original will print msg1 & msg2, then call sys.exit(1)."""
    if 'Could not connect to URL:' in msg1:
        raise ValueError('connection_error')
    if 'Invalid URL:' in msg1:
        raise ValueError('invalid_url')
    if 'Not valid URL:' in msg1:
        raise ValueError('missing_schema')
    raise ValueError('fail')


def mocked_requests_post(*args, **kwargs):
    """Mock requests.post function."""
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code
            self.text = json_data

        def json(self):
            return self.json_data

    if 'connection.error.test' in args[0]:
        raise requests.exceptions.ConnectionError
    if 'invalid.url.test' in args[0]:
        raise requests.exceptions.InvalidURL
    if 'missing.schema.test' in args[0]:
        raise requests.exceptions.MissingSchema
    return MockResponse(None, 404)

@mock.patch('requests.post', side_effect=mocked_requests_post)
@mock.patch('lftools.deploy._log_error_and_exit', side_effect=mocked_log_error)
def test_local_request_post(self, mock_post):
    """Test local_request_post."""
    xml_doc="""
        <promoteRequest>
            <data>
                <stagedRepositoryId>test1-1027</stagedRepositoryId>
                <description>Close staging repository.</description>
            </data>
        </promoteRequest>
        """
    with pytest.raises(ValueError) as excinfo:
        deploy_sys._request_post('connection.error.test', xml_doc, "{'Content-Type': 'application/xml'}")
    assert 'connection_error' in str(excinfo.value)
    with pytest.raises(ValueError) as excinfo:
        deploy_sys._request_post('invalid.url.test:8081nexus', xml_doc, "{'Content-Type': 'application/xml'}")
    assert 'invalid_url' in str(excinfo.value)
    with pytest.raises(ValueError) as excinfo:
        deploy_sys._request_post('http:/missing.schema.test:8081nexus', xml_doc, "{'Content-Type': 'application/xml'}")
    assert 'missing_schema' in str(excinfo.value)
