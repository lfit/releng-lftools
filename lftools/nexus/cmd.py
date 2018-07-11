# -*- code: utf-8 -*-
# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Contains functions for various Nexus tasks."""

import logging
import sys

import yaml

from lftools.nexus import Nexus
from lftools.nexus import util

log = logging.getLogger(__name__)


def reorder_staged_repos(settings_file):
    """Reorder staging repositories in Nexus.

    NOTE: This is a hack for forcing the 'Staging Repositories' repo group
    to be in the correct reverse sorted order. There is a problem with
    Nexus where it is not doing this like it should be.
    """
    with open(settings_file, 'r') as f:
        settings = yaml.safe_load(f)

    for setting in ['nexus', 'user', 'password']:
        if not setting in settings:
            sys.exit('{} needs to be defined'.format(setting))

    _nexus = Nexus(settings['nexus'], settings['user'], settings['password'])

    try:
        repo_id = _nexus.get_repo_group('Staging Repositories')
    except LookupError as e:
        sys.exit("Staging repository 'Staging Repositories' cannot be found")

    repo_details = _nexus.get_repo_group_details(repo_id)

    sorted_repos = sorted(repo_details['repositories'], key=lambda k: k['id'], reverse=True)

    for repos in sorted_repos:
        del repos['resourceURI']
        del repos['name']

    repo_update = repo_details
    repo_update['repositories'] = sorted_repos
    del repo_update['contentResourceURI']
    del repo_update['repoType']

    _nexus.update_repo_group_details(repo_id, repo_update)


def create_repos(config_file, settings_file):
    """Create repositories as defined by configuration file.

    :arg str config: Configuration file containing repository definitions that
        will be used to create the new Nexus repositories.
    :arg str settings: Settings file containing administrative credentials and
        information.
    """
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    with open(settings_file, 'r') as f:
        settings = yaml.safe_load(f)

    for setting in ['nexus', 'user', 'password', 'email_domain']:
        if not setting in settings:
            sys.exit('{} needs to be defined'.format(setting))

    _nexus = Nexus(settings['nexus'], settings['user'], settings['password'])

    def create_nexus_perms(name, targets, email, password, extra_privs=[]):
        # Create target
        try:
            target_id = _nexus.get_target(name)
        except LookupError as e:
            target_id = _nexus.create_target(name, targets)

        # Create privileges
        privs_set = [
                'create',
                'delete',
                'read',
                'update',
            ]

        privs = {}
        for priv in privs_set:
            try:
                privs[priv] = _nexus.get_priv(name, priv)
                log.info('Creating {} privileges.'.format(priv))
            except LookupError as e:
                privs[priv] = _nexus.create_priv(name, target_id, priv)

        # Create Role
        try:
            role_id = _nexus.get_role(name)
            log.info('Creating {} role.'.format(role_id))
        except LookupError as e:
            role_id = _nexus.create_role(name, privs)

        # Create user
        try:
            _nexus.get_user(name)
            log.info('Creating {} user.'.format(name))
        except LookupError as e:
            _nexus.create_user(name, email, role_id, password, extra_privs)

    def build_repo(repo, repoId, config, base_groupId):
        log.info('-> Building for {}.{} in Nexus'.format(base_groupId, repo))
        groupId = '{}.{}'.format(base_groupId, repo)
        target = util.create_repo_target_regex(groupId)

        if 'extra_privs' in config:
            extra_privs = config['extra_privs']
            log.info('Privileges for this repo:' + ', '.join(extra_privs))
        else:
            extra_privs = []

        create_nexus_perms(
            repoId,
            [target],
            settings['email_domain'],
            config['password'],
            extra_privs)

        log.info('-> Finished successfully for {}.{}!!\n'.format(base_groupId, repo))

        if 'repositories' in config:
            for sub_repo in config['repositories']:
                sub_repo_id = "{}-{}".format(repoId, sub_repo)
                build_repo(
                    sub_repo,
                    sub_repo_id,
                    config['repositories'][sub_repo],
                    groupId)

    log.warning('Nexus repo creation started. Aborting now could leave tasks undone!')
    for repo in config['repositories']:
        build_repo(repo, repo, config['repositories'][repo], config['base_groupId'])
