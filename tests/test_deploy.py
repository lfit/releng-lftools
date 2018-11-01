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

@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, 'deploy'),
    )
def test_deploy_archive(cli_runner, datafiles, responses):
    """Test deploy_archives() command for expected upload cases."""
    os.chdir(str(datafiles))
    workspace_dir = os.path.join(str(datafiles), 'workspace')

    # Test successful upload
    url = 'https://nexus.example.org/service/local/repositories/logs/content-compressed'
    responses.add(responses.POST, '{}/test/path/abc'.format(url),
                  json=None, status=201)
    result = cli_runner.invoke(
        cli.cli,
        ['--debug', 'deploy', 'archives', 'https://nexus.example.org', 'test/path/abc', workspace_dir],
        obj={})
    assert result.exit_code == 0

    # Test failed upload
    url = 'https://nexus-fail.example.org/service/local/repositories/logs/content-compressed'
    responses.add(responses.POST, '{}/test/fail/path'.format(url),
                  status=404)
    result = cli_runner.invoke(
        cli.cli,
        ['--debug', 'deploy', 'archives', 'https://nexus-fail.example.org', 'test/fail/path', workspace_dir],
        obj={})
    assert result.exit_code == 1
