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


def get_branches(path=getcwd(), invert=None):
    """Get a list of branches."""
    if invert:
        invert = '--invert-grep'
    if not invert:
        invert = ''
    chdir(path)
    try:
        # noqa
        branches = subprocess.check_output(
            "git branch -r | grep -v origin/HEAD", shell=True)\
            .decode(encoding="UTF-8").split('\n')
        for branch in branches:
            branch = branch.strip()
            # noqa
            hashes = subprocess.check_output(
                'git log {} --no-merges --pretty="%H %ae" --grep "Signed-off-by" {}'
                .format(branch, invert), shell=True)\
                .decode(encoding="UTF-8").split('\n')
        if hashes:
            return hashes
        else:
            return False
    except subprocess.CalledProcessError as e:
        log.error(e)


def check(path=getcwd()):
    """Check repository for commits missing DCO."""
    chdir(path)
    try:
        hashes = get_branches(path)
        if not hashes:
            exit(0)
        else:
            for commit in hashes:
                if commit:
                    log.info("{} is missing 'Signed-off-by' line"
                             .format(commit.split(' ')[0]))
            exit(1)
    except subprocess.CalledProcessError as e:
        log.error(e)


def match(path=getcwd()):
    """Check for commits where DCO does not match the commit author's email."""
    chdir(path)
    try:
        hashes = get_branches(path, invert=False)
        if not hashes:
            exit(0)
        else:
            for commit in hashes:
                commit_id = commit.split(' ')[0]
                if commit_id:
                    # noqa
                    commit_details = subprocess.check_output(
                        "git show --quiet {}"
                        .format(commit_id), shell=True)\
                        .decode(encoding="UTF-8")
                    regex = r'(?=Signed\-off\-by: )[\s\S]*[\<](.*)[\>]'
                    matches = re.findall(regex, commit_details)

                    if matches:
                        continue
                    else:
                        log.info('{} has an author/sign-off mismatch'
                                 .format(commit_id))
            exit(1)
    except subprocess.CalledProcessError as e:
        log.error(e)
