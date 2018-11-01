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

FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'fixtures',
    )


def test_format_url():
    """Test url format."""
    url1="192.168.1.1"
    url2="192.168.1.1:8081"
    url3="192.168.1.1:8081/nexus"
    url4="192.168.1.1:8081/nexus/"
    url5="http://192.168.1.1:8081/nexus"
    url6="https://192.168.1.1:8081/nexus"
    url7="https://192.168.1.1:8081/nexus/"
    url8="www.goodnexussite.org:8081"

    assert deploy_sys2.local_format_url(url1) == 'http://{}'.format(url1)
    assert deploy_sys2.local_format_url(url2) == 'http://{}'.format(url2)
    assert deploy_sys2.local_format_url(url3) == 'http://{}'.format(url3)
    assert deploy_sys2.local_format_url(url4) == 'http://{}'.format(url4)
    assert deploy_sys2.local_format_url(url5) == '{}'.format(url5)
    assert deploy_sys2.local_format_url(url6) == '{}'.format(url6)
    assert deploy_sys2.local_format_url(url7) == '{}'.format(url7)
    assert deploy_sys2.local_format_url(url8) == 'http://{}'.format(url8)


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
