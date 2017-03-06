#!/usr/bin/env python
# -*- code: utf-8 -*-
# vim: sw=4 ts=4 sts=4 et :

#
# NOTE: This is a hack for forcing the 'Staging Repositories' repo group
# to be in the correct reverse sorted order. There is a problem with
# Nexus where it is not doing this like it should be
#

import argparse
import sys
import nexus
import yaml
from operator import itemgetter

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--settings', type=str,
    help='security and settings yaml file')
args = parser.parse_args()

if not args.settings:
    sys.exit('Settings file is required')


# open our settings file
f = open(args.settings, 'r')
settings = yaml.load(f)
f.close()

for setting in ['nexus', 'user', 'password']:
    if not setting in settings:
        sys.exit('{} needs to be defined'.format(setting))

n = nexus.Nexus(settings['nexus'], settings['user'], settings['password'])

try:
    repo_id = n.get_repo_group('Staging Repositories')
except LookupError as e:
    sys.exit("Staging repository 'Staging Repositories' cannot be found")

repo_details = n.get_repo_group_details(repo_id)

sorted_repos = sorted(repo_details['repositories'], key=lambda k: k['id'], reverse=True)

for repos in sorted_repos:
    del repos['resourceURI']
    del repos['name']

repo_update = repo_details
repo_update['repositories'] = sorted_repos
del repo_update['contentResourceURI']
del repo_update['repoType']

n.update_repo_group_details(repo_id, repo_update)
