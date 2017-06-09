# @License EPL-1.0 <http://spdx.org/licenses/EPL-1.0>
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Version bump script for Maven based projects."""

__author__ = 'Thanh Ha'


import os
import subprocess
import sys

import click


@click.group()
@click.pass_context
def version(ctx):
    """Version bump script for Maven based projects.

    In general, versions should be: <major>.<minor>.<micro>[-<human-readable-tag>]

    \b
    - Human readable tag should not have any dots in it
    - SNAPSHOT is used for development

    Scenarios:

        \b
        master before release:        x.y.z-SNAPSHOT (or x.y-SNAPSHOT in which case we treat it as x.y.0-SNAPSHOT)
        at release:                   x.y.z-Helium
        stable/helium after release:  x.y.(z+1)-SNAPSHOT
        master after release:         x.(y+1).0-SNAPSHOT
        Autorelease on master:        <human-readable-tag> is "PreLithium-<date>"
        Autorelease on stable/helium: <human-readable-tag> is "PreHeliumSR1-<date>"
        Release job on master:        <human-readable-tag> is "Lithium"
        Release job on stable/helium: <human-readable-tag> is "HeliumSR1"

    Some things have a date for a version, e.g., 2014.09.24.4

    \b
    * We treat this as YYYY.MM.DD.<minor>
    * Note that all such dates currently in ODL are in YANG tools
    * They are all now YYYY.MM.DD.7 since 7 is the minor version for yangtools
    """
    pass


@click.command()
@click.argument('release-tag')
@click.pass_context
def bump(ctx, release_tag):
    """Version bump pom files in a Maven project by x.(y+1).z or x.y.(z+1).

    This script performs version bumping as follows:

    \b
    1. Change YYYY.MM.DD.y.z-SNAPSHOT to YYYY.MM.DD.(y+1).0-SNAPSHOT
    2. Change YYYY.MM.DD.y.z-Helium to YYMMDD.y.(z+1)-SNAPSHOT
    3. Change x.y.z-SNAPSHOT versions to x.(y+1).0-SNAPSHOT
    4. Change x.y.z-RELEASE_TAG versions to x.y.(z+1)-SNAPSHOT and
    """
    status = subprocess.call(['version', 'bump', release_tag])
    sys.exit(status)


@click.command()
@click.argument('release-tag')
@click.pass_context
def release(ctx, release_tag):
    """Version bump pom files in a Maven project from SNAPSHOT to RELEASE_TAG.

    Searches poms for all instances of SNAPSHOT version and changes it to
    RELEASE_TAG.
    """
    status = subprocess.call(['version', 'release', release_tag])
    sys.exit(status)


@click.command()
@click.argument('release-tag')
@click.argument('patch-dir')
@click.option(
    '--project', default='OpenDaylight',
    help='Project name to use when tagging. (Default: OpenDaylight)')
@click.pass_context
def patch(ctx, release_tag, patch_dir, project):
    """Patch a project with git.bundles and then version bump.

    Applies git.bundle patches to the project and then performs a version bump
    using RELEASE_TAG in order to version bump by x.y.(z+1)-SNAPSHOT.
    """
    if not os.path.isdir(patch_dir):
        print("{} is not a valid directory.".format(patch_dir))
        sys.exit(404)
    status = subprocess.call(['version', 'patch', release_tag, patch_dir, project])
    sys.exit(status)


version.add_command(bump)
version.add_command(patch)
version.add_command(release)
