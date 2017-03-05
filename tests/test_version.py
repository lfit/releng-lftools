import difflib
from distutils import dir_util
import filecmp
import os

import click
import pytest

from lftools import cli


FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'fixtures',
    )


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, 'pom.xml'),
    os.path.join(FIXTURE_DIR, 'pom.xml.expected-bump'),
    )
def test_version_bump(cli_runner, datafiles):
    os.chdir(datafiles)

    # Version bump should bump versions by x.(y+1).z
    result = cli_runner.invoke(cli.cli, ['version', 'bump', 'TestRelease'])
    assert filecmp.cmp('pom.xml', 'pom.xml.expected-bump')


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, 'pom.xml'),
    os.path.join(FIXTURE_DIR, 'pom.xml.expected-release'),
    os.path.join(FIXTURE_DIR, 'pom.xml.expected-release-bump'),
    )
def test_version_release(cli_runner, datafiles):
    os.chdir(datafiles)

    # Version release should modify SNAPSHOT to TestRelease
    result = cli_runner.invoke(cli.cli, ['version', 'release', 'TestRelease'])
    assert filecmp.cmp('pom.xml', 'pom.xml.expected-release')

    # Post release bump should bump versions by x.y.(z+1) and revert back to SNAPSHOT
    result = cli_runner.invoke(cli.cli, ['version', 'bump', 'TestRelease'])
    assert filecmp.cmp('pom.xml', 'pom.xml.expected-release-bump')
