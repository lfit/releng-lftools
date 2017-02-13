#!/usr/bin/env python
# -*- code: utf-8 -*-
# vim: sw=4 ts=4 sts=4 et :

import argparse
import sys
import nexus
import yaml

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--settings', type=str,
    help='security and settings yaml file')
parser.add_argument('-c', '--config', type=str,
    help='configuration to be created')
args = parser.parse_args()

if not args.settings:
    sys.exit('Settings file is required')

if not args.config:
    sys.exit('Config file is required')


# open our settings file
f = open(args.settings, 'r')
settings = yaml.load(f)
f.close()

for setting in ['nexus', 'user', 'password', 'email_domain']:
    if not setting in settings:
        sys.exit('{} needs to be defined'.format(setting))

# open our config file
f = open(args.config, 'r')
config = yaml.load(f)
f.close()

n = nexus.Nexus(settings['nexus'], settings['user'], settings['password'])

def create_nexus_perms(name, targets, email, password, extra_privs=[]):
    # Create target
    try:
        target_id = n.get_target(name)
    except LookupError as e:
        target_id = n.create_target(name, targets)

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
            privs[priv] = n.get_priv(name, priv)
        except LookupError as e:
            privs[priv] = n.create_priv(name, target_id, priv)

    # Create Role
    try:
        role_id = n.get_role(name)
    except LookupError as e:
        role_id = n.create_role(name, privs)

    # Create user
    try:
        n.get_user(name)
    except LookupError as e:
        n.create_user(name, email, role_id, password, extra_privs)

def do_build_repo(repo, repoId, config, base_groupId):
    print('Building for %s.%s' % (base_groupId, repo))
    groupId = '%s.%s' % (base_groupId, repo)
    target = '^/%s/.*' % groupId.replace('.', '[/\.]')
    if 'extra_privs' in config:
        extra_privs = config['extra_privs']
    else:
        extra_privs = []
    create_nexus_perms(repoId, [target], settings['email_domain'],
        config['password'], extra_privs)
    if 'repositories' in config:
        for sub_repo in config['repositories']:
            sub_repo_id = '%s-%s' % (repoId, sub_repo)
            do_build_repo(sub_repo, sub_repo_id, config['repositories'][sub_repo],
                groupId)

for repo in config['repositories']:
    do_build_repo(repo, repo, config['repositories'][repo], config['base_groupId'])
