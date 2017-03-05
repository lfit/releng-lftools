import click
import subprocess

@click.group()
@click.pass_context
@click.version_option()
def cli(ctx):
    pass

###############################################################################
# Shell
###############################################################################

@click.command()
@click.argument('command', type=click.Choice(['bump', 'release']))
@click.argument('release-tag')
@click.pass_context
def version(ctx, command, release_tag):
    """Version bump script for Maven based projects

    Uses *release-tag* to bump versions for Maven projects.

    :arg str command: Version subcommand to call (bump|release)
    :arg str release-tag: When used for the 'release' command it is the
        tag to use to bump all the versions to. When used for the 'bump'
        command it is the tag to determine if a version should be bumped by
        x.1.z.

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
    """
    subprocess.call(['version', command, release_tag])

cli.add_command(version)

if __name__ == '__main__':
    cli(obj={})
