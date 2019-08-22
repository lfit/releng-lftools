# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2018 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Script to check a git repository for commits missing DCO."""

import os

import click
from git import Repo


@click.group()
@click.pass_context
def dco(ctx):
    pass

@click.command()
@click.argument('repo-path', required=True)
@click.option('--strict', type=bool, required=False)
@click.pass_context
def check(ctx, strict, repo_path):
    # Check repository for commits missing DCO."""
    if 'http' in repo_path:
        repo_dir = repo_path.rsplit('/', 1)[-1]
        if os.path.exists(repo_dir) is False:
            repo = Repo.clone_from(url=repo_path, to_path=repo_dir)
        else:
            print("Cannot clone remote repository to directory {} as it already "
                  "exists. Delete it and try again.".format(repo_dir))
            exit(1)
    else:
        repo = Repo(repo_path)

    commits = list(repo.iter_commits())

    for c in commits:
        if strict:
            if 'Signed-off-by' in c.message:
                if c.author.email in c.message:
                    pass
                else:
                    print('Commit {} has DCO mismatch'.format(c))

        if 'Signed-off-by' not in c.message:
            print('Missing DCO in commit {}'.format(c))


dco.add_command(check)
