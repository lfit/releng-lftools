# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2022 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Test git command."""

import configparser
import os

import pytest

from lftools.git.gerrit import Gerrit, Repo

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures")


@pytest.fixture
@pytest.mark.datafiles(os.path.join(FIXTURE_DIR, "git"))
def mock_init(mocker, datafiles):
    creds = {
        "authtype": "basic",
        "username": "myname",
        "password": "mypass",
        "endpoint": "http://gerrit.example.com/r/a/",
        "email": "test@example.com",
    }

    # Clone a sample ci-management repo for use with tests
    remote = "https://gerrit.acumos.org/r/ci-management"
    ciman_dir = os.path.join(str(datafiles), "ci-management")
    os.makedirs(ciman_dir)
    os.chdir(ciman_dir)
    try:
        Repo.clone_from(remote, ciman_dir)
    except Exception as ex:
        print(ex)
        pytest.skip("Could not reach gerrit.acumos.org")
        return None
    Repo.init(ciman_dir)

    mocker.patch("tempfile.mkdtemp", return_value=ciman_dir)
    mocker.patch.object(Gerrit, "get_commit_hook")
    Gerrit.get_commit_hook.start()  # Needed for mocker.stopall() below
    mocker.patch.object(Repo, "clone_from")

    git = Gerrit(creds=creds, fqdn="gerrit.example.com", project="test")

    Gerrit.get_commit_hook.assert_called_once()
    Repo.clone_from.assert_called_once_with("https://myname:mypass@gerrit.example.com/r/a/test", ciman_dir)
    mocker.stopall()
    return git


@pytest.mark.datafiles(os.path.join(FIXTURE_DIR, "git"))
def test_get_commit_hook(mock_init, responses, datafiles):
    if not mock_init:
        pytest.skip("Could not reach gerrit.acumos.org")
        return
    os.chdir(str(datafiles))
    ciman_dir = os.path.join(str(datafiles), "ci-management")
    hook_url = "http://gerrit.example.com/tools/hooks/commit-msg"
    with open("commit-msg", "r") as hook:
        hook_text = hook.read()
    responses.add(responses.GET, hook_url, hook_text)
    mock_init.get_commit_hook("http://gerrit.example.com", ciman_dir)
    with open("ci-management/.git/hooks/commit-msg", "r") as new_hook:
        assert hook_text == new_hook.read()


@pytest.mark.datafiles(os.path.join(FIXTURE_DIR, "git"))
def test_add_info_job(mock_init, datafiles, mocker):
    if not mock_init:
        pytest.skip("Could not reach gerrit.acumos.org")
        return
    fqdn = "gerrit.example.com"
    gerrit_project = "project/subproject"
    issue_id = "TEST-123"
    agent = ""
    commit_msg = "Chore: Automation adds project-subproject.yaml"
    filepath = os.path.join(mock_init.repo.working_tree_dir, "jjb/project-subproject/project-subproject.yaml")
    content = """---
- project:
    name: project-subproject-project-view
    project-name: project-subproject
    views:
      - project-view

- project:
    name: project-subproject-info
    project: project/subproject
    project-name: project-subproject
    build-node: centos7-builder-2c-1g
    branch: master
    jobs:
      - gerrit-info-yaml-verify"""

    mocker.patch.object(Gerrit, "add_file")
    mocker.patch.object(Gerrit, "commit")

    mock_init.add_info_job(fqdn, gerrit_project, issue_id, agent)

    Gerrit.add_file.assert_called_once_with(filepath, content)
    Gerrit.commit.assert_called_once_with(commit_msg, issue_id, push=True)


@pytest.mark.datafiles(os.path.join(FIXTURE_DIR, "git"))
def test_add_git_review(mock_init, datafiles, mocker):
    if not mock_init:
        pytest.skip("Could not reach gerrit.acumos.org")
        return
    fqdn = "gerrit.example.com"
    gerrit_project = "project/subproject"
    issue_id = "TEST-123"
    commit_msg = "Chore: Automation adds .gitreview"
    filepath = ".gitreview"
    content = """[gerrit]
host=gerrit.example.com
port=29418
project=project/subproject
defaultbranch=master"""

    mocker.patch.object(Gerrit, "add_file")
    mocker.patch.object(Gerrit, "commit")

    mock_init.add_git_review(fqdn, gerrit_project, issue_id)

    Gerrit.add_file.assert_called_once_with(filepath, content)
    Gerrit.commit.assert_called_once_with(commit_msg, issue_id, push=True)


@pytest.mark.datafiles(os.path.join(FIXTURE_DIR, "git"))
def test_add_maven_config(mock_init, datafiles, mocker):
    if not mock_init:
        pytest.skip("Could not reach gerrit.acumos.org")
        return
    fqdn = "gerrit.example.com"
    gerrit_project = "project/subproject"
    issue_id = "TEST-123"
    commit_msg = "Chore: Automation adds project/subproject config files"

    creds_path = "jenkins-config/managed-config-files/mavenSettings/project-subproject/serverCredentialMappings.yaml"
    server_creds_content = """---
serverCredentialMappings:
  - serverId: "releases"
    credentialsId: "project-subproject"
  - serverId: "snapshots"
    credentialsId: "project-subproject"
  - serverId: "staging"
    credentialsId: "project-subproject"
  - serverId: "site"
    credentialsId: "project-subproject\""""

    get_setting_mock = mocker.patch("lftools.config.get_setting")
    get_setting_mock.side_effect = configparser.NoOptionError(fqdn, "default_servers")
    mocker.patch.object(Gerrit, "add_symlink")
    mocker.patch.object(Gerrit, "add_file")
    mocker.patch.object(Gerrit, "commit")

    # Test 1 #
    mock_init.add_maven_config(fqdn, gerrit_project, issue_id)
    Gerrit.add_file.assert_called_with(creds_path, server_creds_content)
    Gerrit.commit.assert_called_once_with(commit_msg, issue_id, push=True)

    # Test 2 #
    server_creds_content += """
  - serverId: "nexus3.example.com:10001"
    credentialsId: "project-subproject"
  - serverId: "nexus3.example.com:10002"
    credentialsId: "project-subproject\""""

    mock_init.add_maven_config(fqdn, gerrit_project, issue_id, "nexus3.example.com", "10001,10002")
    Gerrit.add_file.assert_called_with(creds_path, server_creds_content)

    # Test 3 #
    get_setting_mock = mocker.patch("lftools.config.get_setting")

    def setting_response(*args, **kwargs):
        if "additional_credentials" in args:
            return '{"docker.io": "dockerhub-cred"}'
        raise configparser.NoOptionError(fqdn, "default_servers")

    get_setting_mock.side_effect = setting_response

    server_creds_content += """
  - serverId: "docker.io"
    credentialsId: "dockerhub-cred\""""

    mock_init.add_maven_config(fqdn, gerrit_project, issue_id, "nexus3.example.com", "10001,10002")
    Gerrit.add_file.assert_called_with(creds_path, server_creds_content)
