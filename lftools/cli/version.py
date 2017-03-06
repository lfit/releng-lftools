# @License EPL-1.0 <http://spdx.org/licenses/EPL-1.0>
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#
# Contributors:
#   Thanh Ha - Initial implementation
##############################################################################
"""Wrapper for version bash script."""
import os
import subprocess
import sys

import click


@click.group()
@click.pass_context
def version(ctx):
    """Version bump script for Maven based projects.

    Uses *release-tag* to bump versions for Maven projects.

    In general, versions should be: <major>.<minor>.<micro>[-<human-readable-tag>]

    * Human readable tag should not have any dots in it
    * SNAPSHOT is used for development

    Scenarios::

        master before release:        x.y.z-SNAPSHOT (or x.y-SNAPSHOT in which case we treat it as x.y.0-SNAPSHOT)
        at release:                   x.y.z-Helium
        stable/helium after release:  x.y.(z+1)-SNAPSHOT
        master after release:         x.(y+1).0-SNAPSHOT
        Autorelease on master:        <human-readable-tag> is "PreLithium-<date>"
        Autorelease on stable/helium: <human-readable-tag> is "PreHeliumSR1-<date>"
        Release job on master:        <human-readable-tag> is "Lithium"
        Release job on stable/helium: <human-readable-tag> is "HeliumSR1"

    Some things have a date for a version, e.g., 2014.09.24.4

    * We treat this as YYYY.MM.DD.<minor>
    * Note that all such dates currently in ODL are in YANG tools
    * They are all now YYYY.MM.DD.7 since 7 is the minor version for yangtools

    The goal of this script is to:

    #. take all x.y.z-SNAPSHOT to x.y.z-Helium
    #. take all x.y.z-Helium versions to x.y.(z+1)-SNAPSHOT and
    #. take all x.y.z-SNAPSHOT versions to x.(y+1).0-SNAPSHOT

    Commands:

        .. autofunction:: lftools.cli.version.bump
        .. autofunction:: lftools.cli.version.release
        .. autofunction:: lftools.cli.version.patch
    """
    pass

@click.command()
@click.argument('release-tag')
@click.pass_context
def bump(ctx, release_tag):
    """Version bump pom files in a Maven project by x.(y+1).z.

    :arg str release-tag: When used for the 'bump' command it is the tag to
        determine if a version should be bumped by x.(y+1).z (SNAPSHOT) or by
        x.y.(z+1) (release-tag).
    """
    subprocess.call(['version', 'bump', release_tag])


@click.command()
@click.argument('release-tag')
@click.pass_context
def release(ctx, release_tag):
    """Version bump pom files in a Maven project by x.y.(z+1).

    :arg str release-tag: When used for the 'release' command it is the
        tag to use to bump all the versions to.
    """
    subprocess.call(['version', 'release', release_tag])


@click.command()
@click.argument('release-tag')
@click.argument('patch-dir')
@click.option('--project', default='OpenDaylight')
@click.pass_context
def patch(ctx, release_tag, patch_dir, project):
    """Patch a project with git.bundles and then version bump by x.y.(z+1).

    :arg str release-tag: When used for the 'release' command it is the
        tag to use to bump all the versions to. When used for the 'bump'
        command it is the tag to determine if a version should be bumped by
        x.1.z.
    :arg str patch-dir: Path to where the taglist.log and git.bundles are
        stored in the file system.
    """
    if not os.path.isdir(patch_dir):
        print("{} is not a valid directory.".format(patch_dir))
        sys.exit(404)
    subprocess.call(['version', 'patch', release_tag, patch_dir, project])


version.add_command(bump)
version.add_command(patch)
version.add_command(release)
