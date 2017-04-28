# -*- code: utf-8 -*-
"""Unit tests for Github bits."""
import os
from pytest_mock import mocker
from lftools import cli


FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'fixtures/github',
    )
WH_CONFIG_PATH = os.path.join(FIXTURE_DIR,
                              'webhook.example.yaml')
BP_CONFIG_PATH = os.path.join(FIXTURE_DIR,
                              'branch-protection.example.yaml')
ADMIN_CONFIG_PATH = os.path.join(FIXTURE_DIR,
                              'admin-config.example.yaml')
REPO_NAME = "TEST"

def test_cmd_create_webhooks(cli_runner, mocker):
    mock_create_webhooks = mocker.patch('lftools.github.cmd.create_webhooks')
    mock_gh_object = mocker.patch('lftools.github.cmd._get_github_object')
    mock_repo_object = mocker.patch('lftools.github.cmd._get_repo_object')
#    mock_create_hook = mocker.patch('github.Repository.Repository.create_hook')
    cli_runner.invoke(cli.cli, ['github',
                                'create_webhooks',
                                '-c', WH_CONFIG_PATH,
                                '-a', ADMIN_CONFIG_PATH,
                                '-r', REPO_NAME])
    mock_gh_object.return_value = object
    mock_repo_object.return_value = object
    mock_create_webhooks.assert_called_with(WH_CONFIG_PATH, ADMIN_CONFIG_PATH, REPO_NAME)
    calls = [
    ]
    #mock_create_hook.assert_has_calls(calls, any_order=True)
#    mock_create_hook.assert_called()


def test_cmd_protect_branches(cli_runner, mocker):
    mock_protect_branches = mocker.patch('lftools.github.cmd.protect_branches')
    mock_gh_object = mocker.patch('lftools.github.cmd._get_github_object')
    mock_repo_object = mocker.patch('lftools.github.cmd._get_repo_object')
#    mock_protect_branch = mocker.patch('github.Repository.Repository.protect_branch')
    cli_runner.invoke(cli.cli, ['github',
                                'protect_branches',
                                '-c', BP_CONFIG_PATH,
                                '-a', ADMIN_CONFIG_PATH,
                                '-r', REPO_NAME])
    mock_gh_object.return_value = object
    mock_repo_object.return_value = object
    mock_protect_branches.assert_called_with(BP_CONFIG_PATH, ADMIN_CONFIG_PATH, REPO_NAME)
    events = ['event1', 'event2', 'etc']
    config = {'config': {
        'url': 'https://google.com/',
        'content-type': 'json',
        'secret': 'YourSecret'}
             }
#    mock_protect_branch.assert_called()
    #mock_protect_branch.assert_called_with('web',
#                                           config,
#                                           events=events,
#                                           active=False)
