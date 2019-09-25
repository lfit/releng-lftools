# -*- code: utf-8 -*-
# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Functions for DCO check tasks."""

import logging
from os import chdir
from os import getcwd
import re
import subprocess

log = logging.getLogger(__name__)


def get_branches(path=getcwd(), invert=False):
    """Get a list of branches."""
    if invert:
        invert = '--invert-grep'
    else:
        invert = ''
    chdir(path)
    try:
        branches = subprocess.check_output(
            "git branch -r | grep -v origin/HEAD", shell=True)\
            .decode(encoding="UTF-8") \
            .splitlines()
        hashlist = []
        for branch in branches:
            branch = branch.strip()
            hashes = subprocess.check_output(
                'git log {} --no-merges --pretty="%H %ae" --grep "Signed-off-by" {}'
                .format(branch, invert), shell=True)\
                .decode(encoding="UTF-8")\
                .split('\n')
            hashlist = hashlist + hashes
        if hashlist:
            return hashlist
        else:
            return False
    except subprocess.CalledProcessError as e:
        log.error(e)
        exit(1)


def check(path=getcwd()):
    """Check repository for commits missing DCO."""
    chdir(path)
    try:
        hashes = get_branches(path, invert=True)
        if not hashes:
            exit(0)
        else:
            missing = []
            for commit in hashes:
                if commit:
                    missing.append(commit.split(' ')[0])

            # de-dupe the list
            missing_list = list(dict.fromkeys(missing))
            for commit in missing_list:
                log.info("{} is missing 'Signed-off-by' line".format(commit))
            exit(1)
    except subprocess.CalledProcessError as e:
        log.error(e)


def match(path=getcwd()):
    """Check for commits where DCO does not match the commit author's email."""
    chdir(path)
    try:
        hashes = get_branches(path)
        hashes.pop()
        if not hashes:
            exit(0)
        else:
            for commit in hashes:
                commit_id = commit.split(' ')[0]
                if commit_id:
                    commit_details = subprocess.check_output(
                        "git show --quiet {}"
                        .format(commit_id), shell=True)\
                        .decode(encoding="UTF-8")
                    committer_email = subprocess.check_output(
                        "git log --format='%ae' {}^!"
                        .format(commit_id), shell=True)\
                        .decode(encoding="UTF-8").strip()
                    sob_email_regex = '(?=Signed\-off\-by: )[\s\S]*[\<](.*)[\>]'
                    sob_results = re.findall(sob_email_regex, commit_details)

                    if committer_email in sob_results:
                        continue
                    else:
                        print("{} Committer is {} and Signed-off-by is {}."
                              .format(commit_id, committer_email, sob_results))

            exit(1)
    except subprocess.CalledProcessError as e:
        log.error(e)
