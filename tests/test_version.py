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
    os.path.join(FIXTURE_DIR, 'version_bump'),
    )
def test_version_bump(cli_runner, datafiles):
    os.chdir(datafiles)
    result = cli_runner.invoke(cli.cli, ['version', 'bump', 'TestRelease'])

    for _file in datafiles.listdir():
        pom = str(_file) + '/pom.xml'
        expected_pom = str(_file) + '/pom.xml.expected'
        assert filecmp.cmp(pom, expected_pom)


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, 'version_release'),
    )
def test_version_release(cli_runner, datafiles):
    os.chdir(datafiles)
    result = cli_runner.invoke(cli.cli, ['version', 'release', 'TestRelease'])

    for _file in datafiles.listdir():
        pom = str(_file) + '/pom.xml'
        expected_pom = str(_file) + '/pom.xml.expected'
        assert filecmp.cmp(pom, expected_pom)
