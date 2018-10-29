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
from requests.exceptions import ConnectionError, MissingSchema, InvalidURL

from lftools import cli
import lftools.deploy as deploy_sys
try:
    import mock
except ImportError:
    from unittest import mock
import requests

FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'fixtures',
    )


def test_format_url():
    """Test url format."""
    test_url=[["192.168.1.1", "http://192.168.1.1"],
         ["192.168.1.1:8081", "http://192.168.1.1:8081"],
         ["192.168.1.1:8081/nexus", "http://192.168.1.1:8081/nexus"],
         ["192.168.1.1:8081/nexus/", "http://192.168.1.1:8081/nexus"],
         ["http://192.168.1.1:8081/nexus", "http://192.168.1.1:8081/nexus"],
         ["https://192.168.1.1:8081/nexus", "https://192.168.1.1:8081/nexus"],
         ["https://192.168.1.1:8081/nexus/", "https://192.168.1.1:8081/nexus"],
         ["www.goodnexussite.org:8081", "http://www.goodnexussite.org:8081"],
         ["192.168.1.1:8081/nexus///", "http://192.168.1.1:8081/nexus"]]

    for url in test_url:
        assert deploy_sys._format_url(url[0]) == url[1]


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


def test_log_and_exit():
    """Test exit."""
    with pytest.raises(SystemExit) as excinfo:
        deploy_sys._log_error_and_exit("testmsg")
    assert excinfo.type == SystemExit

def test_format_url():
    """Test url format."""
    test_url=[["192.168.1.1", "http://192.168.1.1"],
         ["192.168.1.1:8081", "http://192.168.1.1:8081"],
         ["192.168.1.1:8081/nexus", "http://192.168.1.1:8081/nexus"],
         ["192.168.1.1:8081/nexus/", "http://192.168.1.1:8081/nexus"],
         ["http://192.168.1.1:8081/nexus", "http://192.168.1.1:8081/nexus"],
         ["https://192.168.1.1:8081/nexus", "https://192.168.1.1:8081/nexus"],
         ["https://192.168.1.1:8081/nexus/", "https://192.168.1.1:8081/nexus"],
         ["www.goodnexussite.org:8081", "http://www.goodnexussite.org:8081"],
         ["192.168.1.1:8081/nexus///", "http://192.168.1.1:8081/nexus"]]

    for url in test_url:
        assert deploy_sys._format_url(url[0]) == url[1]

def test_get_node_from_xml():
    """Test extracting from xml."""
    document = """\
        <slideshow>
        <title>Demo slideshow</title>
        <slide><title>Slide title</title>
        <point>This is a demo</point>
        <point>Of a program for processing slides</point>
        </slide>

        <slide><title>Another demo slide</title><stagedRepositoryId>432</stagedRepositoryId><point>It is important</point>
        <point>To have more than</point>
        <point>one slide</point>
        </slide>
        </slideshow>
        """
    assert deploy_sys._get_node_from_xml(document, 'stagedRepositoryId') == '432'
    with pytest.raises(SystemExit) as excinfo:
        deploy_sys._get_node_from_xml(document, 'NotFoundTag')
    assert excinfo.type == SystemExit

def mocked_log_error(msg1=None, msg2=None):
    """Mock _log_error_and_exit function.
    This function is modified to simply raise an Exception.
    The original will print msg1 & msg2, then call sys.exit(1)."""
    if 'Could not connect to URL:' in msg1:
        raise ValueError('connection_error')
    if 'Invalid URL:' in msg1:
        raise ValueError('invalid_url')
    if 'Not valid URL:' in msg1:
        raise ValueError('missing_schema')
    if "profile with id '93fb68073c18a' does not exist" in msg1:
        raise ValueError('profile.id.not.exist')
    if "OTHER create error" in msg1:
        raise ValueError('other.create.error')
    if "HTTP method POST is not supported by this URL" in msg1:
        raise ValueError('post.not.supported')
    if "Did not find nexus site" in msg1:
        raise ValueError('site.not.found')
    if "Failed with status code " in msg1:
        raise ValueError('other.error.occured')
    if "Staging repository do not exist." in msg1:
        raise ValueError('missing.staging.repository')
    if "Staging repository is already closed." in msg1:
        raise ValueError('staging.already.closed')
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
    closed_already = """
        <nexus-error>
            <errors>
                <error>
                    <id>*</id>
                    <msg>Unhandled: Repository: test1-1027 has invalid state: closed</msg>
                </error>
            </errors>
        </nexus-error>
        """
    dont_exist = """
        <nexus-error>
            <errors>
                <error>
                    <id>*</id>
                    <msg>Unhandled: Missing staging repository: test1-1034</msg>
                </error>
            </errors>
        </nexus-error>
        """
    created = """
        <promoteResponse>
            <data>
                <stagedRepositoryId>test1-1030</stagedRepositoryId>
                <description>Create staging repository.</description>
            </data>
        </promoteResponse>
        """
    profile_id_dont_exist = """
        <nexus-error>
            <errors>
                <error>
                    <id>*</id>
                    <msg>Cannot create Staging Repository, profile with id &apos;93fb68073c18a&apos; does not exist.</msg>
                </error>
            </errors>
        </nexus-error>
        """
    other_create_error = """
        <nexus-error>
            <errors>
                <error>
                    <id>*</id>
                    <msg>OTHER create error.</msg>
                </error>
            </errors>
        </nexus-error>
        """
    post_not_supported = """
        <html>
            <head>
                <title>405 - HTTP method POST is not supported by this URL</title>
                <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>

                <link rel="icon" type="image/png" href="http://192.168.1.26:8081/nexus/favicon.png">
                <!--[if IE]>
                <link rel="SHORTCUT ICON" href="http://192.168.1.26:8081/nexus/favicon.ico"/>
                <![endif]-->

                <link rel="stylesheet" href="http://192.168.1.26:8081/nexus/static/css/Sonatype-content.css?2.14.10-01" type="text/css" media="screen" title="no title" charset="utf-8">
            </head>
            <body>
                <h1>405 - HTTP method POST is not supported by this URL</h1>
                <p>HTTP method POST is not supported by this URL</p>
            </body>
        </html>
        """
    site_not_found = """
        <html>
            <head>
                <title>404 - Site Not Found</title>
            </head>
            <body>
                <h1>404 - Site not found</h1>
            </body>
        </html>
        """
    other_error_occured = """
        <html>
            <head>
                <title>303 - See Other</title>
            </head>
            <body>
                <h1>303 - See Other</h1>
            </body>
        </html>
        """
    missing_staging_repository = """
        <nexus-error>
            <errors>
                <error>
                    <id>*</id>
                    <msg>Unhandled: Missing staging repository: test1-1</msg>
                </error>
            </errors>
        </nexus-error>
        """
    staging_already_closed = """
        <nexus-error>
            <errors>
                <error>
                    <id>*</id>
                    <msg>Unhandled: Repository: test1-1000 has invalid state: closed</msg>
                </error>
            </errors>
        </nexus-error>
    """
    if 'connection.error.test' in args[0]:
        raise requests.exceptions.ConnectionError
    if 'invalid.url.test' in args[0]:
        raise requests.exceptions.InvalidURL
    if 'missing.schema.test' in args[0]:
        raise requests.exceptions.MissingSchema
    if 'valid.create.post' in args[0]:
        return MockResponse(created, 201)
    if 'profile.id.not.exist' in args[0]:
        return MockResponse(profile_id_dont_exist, 404)
    if 'other.create.error' in args[0]:
        return MockResponse(other_create_error, 404)
    if 'post.not.supported' in args[0]:
        return MockResponse(post_not_supported, 405)
    if 'site.not.found' in args[0]:
        return MockResponse(site_not_found, 404)
    if 'other.error.occured' in args[0]:
        return MockResponse(other_error_occured, 303)
    if 'missing.staging.repository' in args[0]:
        return MockResponse(missing_staging_repository, 500)
    if 'staging.already.closed' in args[0]:
        return MockResponse(staging_already_closed, 500)
    return MockResponse(None, 404)

@mock.patch('requests.post', side_effect=mocked_requests_post)
@mock.patch('lftools.deploy._log_error_and_exit', side_effect=mocked_log_error)
def test__request_post(self, mock_post):
    """Test _request_post."""
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

@mock.patch('requests.post', side_effect=mocked_requests_post)
@mock.patch('lftools.deploy._log_error_and_exit', side_effect=mocked_log_error)
def test_nexus_stage_repo_create(self, mock_post):
    """Test nexus_stage_repo_create."""
    res = deploy_sys.nexus_stage_repo_create('valid.create.post', '93fb68073c18')
    assert res == 'test1-1030'
    with pytest.raises(ValueError) as excinfo:
        res = deploy_sys.nexus_stage_repo_create('profile.id.not.exist', 'INVALID')
    assert 'profile.id.not.exist' in str(excinfo.value)
    with pytest.raises(ValueError) as excinfo:
        res = deploy_sys.nexus_stage_repo_create('other.create.error', 'INVALID')
    assert 'other.create.error' in str(excinfo.value)
    with pytest.raises(ValueError) as excinfo:
        res = deploy_sys.nexus_stage_repo_create('post.not.supported', 'INVALID')
    assert 'post.not.supported' in str(excinfo.value)
    with pytest.raises(ValueError) as excinfo:
        res = deploy_sys.nexus_stage_repo_create('site.not.found', 'INVALID')
    assert 'site.not.found' in str(excinfo.value)
    with pytest.raises(ValueError) as excinfo:
        res = deploy_sys.nexus_stage_repo_create('other.error.occured', 'INVALID')
    assert 'other.error.occured' in str(excinfo.value)

@mock.patch('requests.post', side_effect=mocked_requests_post)
@mock.patch('lftools.deploy._log_error_and_exit', side_effect=mocked_log_error)
def test_nexus_stage_repo_close(self, mock_post):
    """Test nexus_stage_repo_close."""
    deploy_sys.nexus_stage_repo_close('valid.create.post', '93fb68073c18', 'test1-1027')
    with pytest.raises(ValueError) as excinfo:
        deploy_sys.nexus_stage_repo_close('site.not.found', 'INVALID', 'test1-1027')
    assert 'site.not.found' in str(excinfo.value)
    with pytest.raises(ValueError) as excinfo:
        deploy_sys.nexus_stage_repo_close('missing.staging.repository', 'INVALID',  'test1-1027')
    assert 'missing.staging.repository' in str(excinfo.value)
    with pytest.raises(ValueError) as excinfo:
        deploy_sys.nexus_stage_repo_close('staging.already.closed', 'INVALID',  'test1-1027')
    assert 'staging.already.closed' in str(excinfo.value)
    with pytest.raises(ValueError) as excinfo:
        deploy_sys.nexus_stage_repo_close('other.error.occured', 'INVALID', 'test1-1027')
    assert 'other.error.occured' in str(excinfo.value)
