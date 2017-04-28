# -*- code: utf-8 -*-
"""Github tools cmd module"""
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

from github import Github, Repository
import yaml 
import sys

def github(settings_file):
    """
    Sets up an authenticated Github User with the base github
    api url and a personal access token.
    """

    with open(settings_file, 'r') as settings_f:
        settings = yaml.safe_load(settings_f)

    for setting in ['base_url', 'token']:
        if not setting in settings:
            sys.exit('{} needs to be defined'.format(setting))

    return Github(settings['token'], base_url=settings['base_url'])

def protect_branch(branch_name, repo):
    """Add branch protections"""
    pass

def create_webhooks(config_file, settings_file):
    """
    Create a webhook via the Github api
    """

    gh_object = github(settings_file)
    repo = gh_object.get_user().get_repo()

    with open(config_file, 'r') as config_f:
        configs = yaml.safe_load(config_f)

    for hook in configs:
        for key in hook:
            try:
                repo.create_hook(hook[key]['name'],
                                 hook[key]['config'],
                                 events=hook[key]['events'],
                                 active=hook[key]['active'])
            except KeyError as error:
                sys.exit('Key Error: {}'.format(error))



