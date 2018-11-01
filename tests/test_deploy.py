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

def mocked_log_error(msg1=None, msg2=None):
    """Mock local_log_error_and_exit function.
    This function is modified to simply raise an Exception.
    The original will print msg1 & msg2, then call sys.exit(1)."""
    print ("in log_error {}".format(msg1))
    if 'Could not connect to URL:' in msg1:
        raise ValueError('connection_error')
    if 'Invalid URL:' in msg1:
        raise ValueError('invalid_url')
    if 'Not valid URL:' in msg1:
        raise ValueError('missing_schema')
    if 'ZIP file not found' in msg1:
        raise ValueError('zipfile_not_found')
    if 'Can not read ZIP file, wrong permissions:' in msg1:
        raise ValueError('zipfile_wrong_permission')
    if 'Repository is read only' in msg1:
        raise ValueError('read_only_repo')
    if 'Did not find repository with id' in msg1:
        raise ValueError('repo_not_found')
    if 'Failed to upload with' in msg1:
        raise ValueError('other_weird_error')
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
    read_only_repo = """
        <html>
            <head>
                <title>400 - Bad Request</title>
                <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>


                <link rel="icon" type="image/png" href="http://192.168.1.26:8081/nexus/favicon.png">
                <!--[if IE]>
                <link rel="SHORTCUT ICON" href="http://192.168.1.26:8081/nexus/favicon.ico"/>
                <![endif]-->

                <link rel="stylesheet" href="http://192.168.1.26:8081/nexus/static/css/Sonatype-content.css?2.14.10-01" type="text/css" media="screen" title="no title" charset="utf-8">
            </head>
            <body>
                <h1>400 - Bad Request</h1>
                <p>Repository with ID='central' is Read Only, but action was 'create'!</p>
            </body>
        </html>
        """
    repo_not_found = """
        <html>
            <head>
                <title>404 - Not Found</title>
                <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>


                <link rel="icon" type="image/png" href="http://192.168.1.26:8081/nexus/favicon.png">
                <!--[if IE]>
                <link rel="SHORTCUT ICON" href="http://192.168.1.26:8081/nexus/favicon.ico"/>
                <![endif]-->

                <link rel="stylesheet" href="http://192.168.1.26:8081/nexus/static/css/Sonatype-content.css?2.14.10-01" type="text/css" media="screen" title="no title" charset="utf-8">
            </head>
            <body>
                <h1>404 - Not Found</h1>
                <p>Repository with ID=&quot;snapshots1&quot; not found</p>
            </body>
        </html>
        """
    other_weird_error = """
        <html>
            <head>
                <title>503 - Service Unavailable</title>
                <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>


                <link rel="icon" type="image/png" href="http://192.168.1.26:8081/nexus/favicon.png">
                <!--[if IE]>
                <link rel="SHORTCUT ICON" href="http://192.168.1.26:8081/nexus/favicon.ico"/>
                <![endif]-->

                <link rel="stylesheet" href="http://192.168.1.26:8081/nexus/static/css/Sonatype-content.css?2.14.10-01" type="text/css" media="screen" title="no title" charset="utf-8">
            </head>
            <body>
                <h1>503 - Service Unavailable</h1>
                <p>Service is unavailable at this time</p>
            </body>
        </html>
        """
    print ("in requests.post {}".format(args[0]))
    if 'deploy.zip.ok' in args[0]:
        return MockResponse(None, 201)
    if 'zipfile.not.found' in args[0]:
        raise FileNotFoundError
    if 'zipfile.wrong.permission' in args[0]:
        raise PermissionError
    if 'read.only.repo' in args[0]:
        return MockResponse(read_only_repo, 400)
    if 'repo.not.found' in args[0]:
        return MockResponse(repo_not_found, 404)
    if 'other.weird.error' in args[0]:
        return MockResponse(other_weird_error, 503)
    return MockResponse(None, 404)

@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, 'deploy'),
    )
@mock.patch('requests.post', side_effect=mocked_requests_post)
@mock.patch('lftools.deploy._log_error_and_exit', side_effect=mocked_log_error)
def test_deploy_nexus_zip(self, mock_post, datafiles):
    """Test deploy_nexus_zip."""
    os.chdir(str(datafiles))
    workspace_dir = os.path.join(str(datafiles), 'zip-test-files')
    real_zip_file=os.path.join(workspace_dir, 'test.zip')
    not_found_zip_file=os.path.join(workspace_dir, 'not_found_test.zip')
    deploy_sys.deploy_nexus_zip('deploy.zip.ok', 'snapshots', 'aaf', real_zip_file)

    with pytest.raises(ValueError) as excinfo:
        deploy_sys.deploy_nexus_zip('zipfile.not.found', 'snapshots', 'aaf', not_found_zip_file)
    assert 'zipfile_not_found' in str(excinfo.value)

    os.chmod(real_zip_file, 0o000)
    with pytest.raises(ValueError) as excinfo:
        deploy_sys.deploy_nexus_zip('zipfile.wrong.permission', 'snapshots', 'aaf', real_zip_file)
    res = False
    if 'zipfile_wrong_permission' in str(excinfo.value):
        res = True
    if 'zipfile_not_found' in str(excinfo.value):
        res = True
    assert res == True
    os.chmod(real_zip_file, 0o755)

    with pytest.raises(ValueError) as excinfo:
        deploy_sys.deploy_nexus_zip('read.only.repo', 'snapshots', 'aaf', real_zip_file)
    assert 'read_only_repo' in str(excinfo.value)
    with pytest.raises(ValueError) as excinfo:
        deploy_sys.deploy_nexus_zip('repo.not.found', 'snapshots', 'aaf', real_zip_file)
    assert 'repo_not_found' in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        deploy_sys.deploy_nexus_zip('other.weird.error', 'snapshots', 'aaf', real_zip_file)
    assert 'other_weird_error' in str(excinfo.value)
