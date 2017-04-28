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

def github():
    return Github()

def protect_branch(branch_name, repo):
    """Add branch protections"""
    pass

def create_webhooks(config):
    gh = github()
    repo = gh.get_user().get_repo()

    with open(config, 'r') as config_file:
        config = yaml.safe_load(config_file)

    for hook in config:
        for key in hook:
            try:
                repo.create_hook(hook[key]['name'],
                                 hook[key]['config'],
                                 events=hook[key]['events'],
                                 active=hook[key]['active'])
            except KeyError as error:
                sys.exit('Key Error: {}'.format(error))



