# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2018 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Push or Promote artifacts to packagecloud repositories."""

__author__ = 'Houa Yang'

import logging
import subprocess
import os
import sys

import click

log = logging.getLogger(__name__)


@click.group()
@click.pass_context
def packagecloud_cli(ctx):
    """PackageCloud CLI"""
    pass

@click.command(name='push')
@click.argument('user')
@click.argument('repo')
@click.argument('distro_version')
@click.argument('artifact')
@click.pass_context
def packagecloud_push(ctx, user, repo, distro_version, artifact):
    """Push artifacts to packagecloud.

    USER: username listed in packagecloud account ex: o-ran-sc

    REPO: repo name ex: stage

    Distro: distro ex: el/7

    Artifact: artifact with/without path to be pushed
              ex: tree-1.6.0-10.el7.x86_64.rpm or
              $WORKSPACE/test/ex: tree-1.6.0-10.el7.x86_64.rpm
    """
    log.info("Pushing {} to {}/{} using user {}".format(artifact, repo, distro_version, user))
    os.system('package_cloud push {}/{}/{} {}'.format(user, repo, distro_version, artifact))
    #subprocess.run(["package_cloud", "push", "{}/{}/{} {}".format(user, repo, distro, artifact)], stdout.decode('utf-8'))


@click.command(name='promote')
@click.argument('user')
@click.argument('source_repo')
@click.argument('distro_version')
@click.argument('artifact')
@click.argument('destination_repo')
@click.pass_context
def packagecloud_promote(ctx, user, source_repo, distro_version, artifact, destination_repo):
    """Promotes artifacts in packagecloud.

    USER: username listed in packagecloud account ex: o-ran-sc

    SOURCE_REPO: repo to promte from ex: stage

    DISTRO-VERSION: distro ex: el/7

    ARTIFACT: name of the artifact in the source repo
              ex: tree-1.6.0-10.el7.x86_64.rpm

    DESTINATION_REPO: repo to promote to ex: release
    """
    log.info("Promoting {} from {} to {} using user {}".format(artifact, source_repo, destination_repo, user))
    os.system('package_cloud promote {}/{}/{} {} {}/{}/{}'.format(user, source_repo, distro_version, artifact, user, destination_repo, distro_version))


packagecloud_cli.add_command(packagecloud_push)
packagecloud_cli.add_command(packagecloud_promote)