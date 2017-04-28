# -*- code: utf-8 -*-
"""Github tools cmd module."""
# @License EPL-1.0 <http://spdx.org/licenses/EPL-1.0>
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################

__author__ = 'Jeremy Phelps'
import sys

from github import Github
import yaml


def github_user(admin_config_file):
    """Set up an authenticated Github User.

    arg string settings_file: Path to settings file
    containing Github api URL and token.
    """
    with open(admin_config_file, 'r') as admin_config_f:
        admin_config = yaml.safe_load(admin_config_f)

    for setting in ['base_url', 'token']:
        if not setting in admin_config:
            sys.exit('{} needs to be defined'.format(setting))

    return Github(admin_config['token'], base_url=admin_config['base_url'])


def _get_github_object(admin_config_file):
    return github_user(admin_config_file)


def _get_repo_object(gh_object, repo_name):
    return gh_object.get_user().get_repo(repo_name)


def protect_branches(config_file, admin_config_file, repo_name):
    """Protect repository branches via the Github api."""
    gh_object = _get_github_object(admin_config_file)
    repo_object = _get_repo_object(gh_object, repo_name)
    with open(config_file, 'r') as config_f:
        configs = yaml.safe_load(config_f)

    # do stuff with configs here
    with open(config_file, 'r') as config_f:
        configs = yaml.safe_load(config_f)

    for hook in configs:
        for key in hook:
            try:
                branch_name = hook[key]['name']
                enabled = hook[key]['enabled']
                enforcement_level = hook[key]['required_status_checks']['strict']
                contexts = hook[key]['required_status_checks']['contexts']
                repo_object.protect_branch(branch_name,
                                           enabled,
                                           enforcement_level=enforcement_level,
                                           contexts=contexts)
            except KeyError as error:
                sys.exit('Key Error: {}'.format(error))


def create_webhooks(config_file, admin_config_file, repo_name):
    """Create a webhook via the Github api."""
    gh_object = _get_github_object(admin_config_file)
    repo_object = _get_repo_object(gh_object, repo_name)
    with open(config_file, 'r') as config_f:
        configs = yaml.safe_load(config_f)

    for hook in configs:
        for key in hook:
            try:
                repo_object.create_hook(hook[key]['name'],
                                        hook[key]['config'],
                                        events=hook[key]['events'],
                                        active=hook[key]['active'])
            except KeyError as error:
                sys.exit('Key Error: {}'.format(error))
