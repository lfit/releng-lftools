# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2018 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Test deploy command."""

import os
import sys

import pytest
import requests

from lftools import cli
import lftools.deploy as deploy_sys


FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'fixtures',
    )


def test_log_and_exit():
    """Test exit."""
    with pytest.raises(SystemExit) as excinfo:
        deploy_sys._log_error_and_exit("testmsg")
    assert excinfo.type == SystemExit


def test_format_url():
    """Test url format."""
    test_url=[["192.168.1.1", "http://192.168.1.1"],
         ["192.168.1.1:8081", "http://192.168.1.1:8081"],
         ["192.168.1.1:8081/nexus", "http://192.168.1.1:8081/nexus"],
         ["192.168.1.1:8081/nexus/", "http://192.168.1.1:8081/nexus"],
         ["http://192.168.1.1:8081/nexus", "http://192.168.1.1:8081/nexus"],
         ["https://192.168.1.1:8081/nexus", "https://192.168.1.1:8081/nexus"],
         ["https://192.168.1.1:8081/nexus/", "https://192.168.1.1:8081/nexus"],
         ["www.goodnexussite.org:8081", "http://www.goodnexussite.org:8081"],
         ["192.168.1.1:8081/nexus///", "http://192.168.1.1:8081/nexus"]]

    for url in test_url:
        assert deploy_sys._format_url(url[0]) == url[1]


def test_log_and_exit():
    """Test exit."""
    with pytest.raises(SystemExit) as excinfo:
        deploy_sys._log_error_and_exit("testmsg")
    assert excinfo.type == SystemExit


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, 'deploy'),
    )
def test_copy_archive_dir(cli_runner, datafiles):
    """Test copy_archives() command to ensure archives dir is copied."""
    os.chdir(str(datafiles))
    workspace_dir = os.path.join(str(datafiles), 'workspace')
    stage_dir = str(datafiles.mkdir("stage_archive"))

    os.chdir(stage_dir)
    result = cli_runner.invoke(
        cli.cli,
        ['--debug', 'deploy', 'copy-archives', workspace_dir],
        obj={})
    assert result.exit_code == 0

    assert os.path.exists(os.path.join(stage_dir, 'test.log'))


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, 'deploy'),
    )
def test_copy_archive_pattern(cli_runner, datafiles):
    """Test copy_archives() command to ensure glob patterns are copied."""
    os.chdir(str(datafiles))
    workspace_dir = os.path.join(str(datafiles), 'workspace')
    stage_dir = str(datafiles.mkdir("stage_archive"))

    os.chdir(stage_dir)
    result = cli_runner.invoke(
        cli.cli,
        ['--debug', 'deploy', 'copy-archives', workspace_dir, '**/*.txt'],
        obj={})
    assert result.exit_code == 0

    assert os.path.exists(os.path.join(stage_dir, 'test.log'))
    assert os.path.exists(os.path.join(stage_dir, 'abc.txt'))
    assert not os.path.exists(os.path.join(stage_dir, 'dependencies.log'))
    assert os.path.exists(os.path.join(
        stage_dir, 'aaa', 'aaa-cert', 'target', 'surefire-reports',
        'org.opendaylight.aaa.cert.test.AaaCertMdsalProviderTest-output.txt'))


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, 'deploy'),
    )
def test_deploy_archive(cli_runner, datafiles, responses):
    """Test deploy_archives() command for expected upload cases."""
    os.chdir(str(datafiles))
    workspace_dir = os.path.join(str(datafiles), 'workspace')

    # Test successful upload
    url = 'https://nexus.example.org/service/local/repositories/logs/content-compressed'
    responses.add(responses.POST, '{}/test/path/abc'.format(url),
                  json=None, status=201)
    result = cli_runner.invoke(
        cli.cli,
        ['--debug', 'deploy', 'archives', 'https://nexus.example.org', 'test/path/abc', workspace_dir],
        obj={})
    assert result.exit_code == 0

    # Test failed upload
    url = 'https://nexus-fail.example.org/service/local/repositories/logs/content-compressed'
    responses.add(responses.POST, '{}/test/fail/path'.format(url),
                  status=404)
    result = cli_runner.invoke(
        cli.cli,
        ['--debug', 'deploy', 'archives', 'https://nexus-fail.example.org', 'test/fail/path', workspace_dir],
        obj={})
    assert result.exit_code == 1

@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, 'deploy'),
    )
def test_deploy_logs(cli_runner, datafiles, responses):
    """Test deploy_logs() command for expected upload cases."""
    os.chdir(str(datafiles))
    workspace_dir = os.path.join(str(datafiles), 'workspace')

    # Test successful upload
    build_url = 'https://jenkins.example.org/job/builder-check-poms/204'
    nexus_url = 'https://nexus.example.org/service/local/repositories/logs/content-compressed'
    responses.add(responses.GET, '{}/consoleText'.format(build_url),
                  status=201)
    responses.add(responses.GET, '{}/timestamps?time=HH:mm:ss&appendLog'.format(build_url),
                  body='This is a console timestamped log.', status=201)
    responses.add(responses.POST, '{}/test/log/upload'.format(nexus_url), status=201)
    result = cli_runner.invoke(
        cli.cli,
        ['--debug', 'deploy', 'logs', 'https://nexus.example.org', 'test/log/upload', build_url],
        obj={})
    assert result.exit_code == 0


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, 'deploy'),
    )
def test_deploy_nexus_zip(cli_runner, datafiles, responses):
    os.chdir(str(datafiles))
    nexus_url = 'https://nexus.example.org'
    nexus_repo = 'test-repo'
    nexus_path = 'test/path'

    # Test success
    success_upload_url = '{}/service/local/repositories/{}/content-compressed/{}'.format(
        nexus_url,
        nexus_repo,
        nexus_path,
    )
    responses.add(responses.POST, success_upload_url,
                  status=201)
    result = cli_runner.invoke(
        cli.cli,
        ['--debug', 'deploy', 'nexus-zip', 'https://nexus.example.org', 'test-repo', 'test/path', 'zip-test-files/test.zip'],
        obj={})
    assert result.exit_code == 0

    # Test repository 404
    upload_404 = """<html>
  <head>
    <title>404 - Not Found</title>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>


    <link rel="icon" type="image/png" href="https://nexus.opendaylight.org/favicon.png">
    <!--[if IE]>
    <link rel="SHORTCUT ICON" href="https://nexus.opendaylight.org/favicon.ico"/>
    <![endif]-->

    <link rel="stylesheet" href="https://nexus.opendaylight.org/static/css/Sonatype-content.css?2.14.7-01" type="text/css" media="screen" title="no title" charset="utf-8">
  </head>
  <body>
    <h1>404 - Not Found</h1>
    <p>Repository with ID=&quot;logs2&quot; not found</p>
  </body>
</html>
"""
    upload_404_url = '{}/service/local/repositories/{}/content-compressed/{}'.format(
        nexus_url,
        'logs2',
        nexus_path,
    )
    responses.add(responses.POST, upload_404_url,
                  body=upload_404, status=404)
    result = cli_runner.invoke(
        cli.cli,
        ['--debug', 'deploy', 'nexus-zip', 'https://nexus.example.org', 'logs2', 'test/path', 'zip-test-files/test.zip'],
        obj={})
    assert result.exit_code == 1


def test_get_node_from_xml():
    """Test extracting from xml."""
    document = """\
        <slideshow>
        <title>Demo slideshow</title>
        <slide><title>Slide title</title>
        <point>This is a demo</point>
        <point>Of a program for processing slides</point>
        </slide>

        <slide><title>Another demo slide</title><stagedRepositoryId>432</stagedRepositoryId><point>It is important</point>
        <point>To have more than</point>
        <point>one slide</point>
        </slide>
        </slideshow>
        """
    assert deploy_sys._get_node_from_xml(document, 'stagedRepositoryId') == '432'
    with pytest.raises(SystemExit) as excinfo:
        deploy_sys._get_node_from_xml(document, 'NotFoundTag')
    assert excinfo.type == SystemExit


def mocked_log_error(*msg_list):
    """Mock _log_error_and_exit function.
    This function is modified to simply raise an Exception.
    The original will print msg1 & msg2, then call sys.exit(1)."""
    msg1=msg_list[0]
    if 'Could not connect to URL:' in msg1:
        raise ValueError('connection_error')
    if 'Invalid URL:' in msg1:
        raise ValueError('invalid_url')
    if 'Not valid URL:' in msg1:
        raise ValueError('missing_schema')
    if "profile with id 'INVALID' does not exist" in msg1:
        raise ValueError('profile.id.not.exist')
    if "OTHER create error" in msg1:
        raise ValueError('other.create.error')
    if "HTTP method POST is not supported by this URL" in msg1:
        raise ValueError('post.not.supported')
    if "Did not find nexus site" in msg1:
        raise ValueError('site.not.found')
    if "Failed with status code " in msg1:
        raise ValueError('other.error.occured')
    if "Staging repository do not exist." in msg1:
        raise ValueError('missing.staging.repository')
    if "Staging repository is already closed." in msg1:
        raise ValueError('staging.already.closed')
    raise ValueError('fail')


def test__request_post(responses, mocker):
    """Test _request_post."""
    mocker.patch('lftools.deploy._log_error_and_exit', side_effect=mocked_log_error)
    xml_doc="""
        <promoteRequest><data>
            <stagedRepositoryId>test1-1027</stagedRepositoryId>
            <description>Close staging repository.</description>
        </data></promoteRequest>
        """
    headers = {'Content-Type': 'application/xml'}

    test_url='http://connection.error.test'
    exception = requests.exceptions.ConnectionError(test_url)
    responses.add(responses.POST, test_url, body=exception)
    with pytest.raises(ValueError) as excinfo:
        deploy_sys._request_post(test_url, xml_doc, headers)
    assert 'connection_error' in str(excinfo.value)

    test_url='http://invalid.url.test:8081'
    exception = requests.exceptions.InvalidURL(test_url)
    responses.add(responses.POST, test_url, body=exception)
    with pytest.raises(ValueError) as excinfo:
        deploy_sys._request_post(test_url, xml_doc, headers)
    assert 'invalid_url' in str(excinfo.value)

    test_url='http://missing.schema.test:8081'
    exception = requests.exceptions.MissingSchema(test_url)
    responses.add(responses.POST, test_url, body=exception)
    with pytest.raises(ValueError) as excinfo:
        deploy_sys._request_post(test_url, xml_doc, headers)
    assert 'missing_schema' in str(excinfo.value)

def test__request_post_file(responses, mocker):
    """Test _request_post_file."""

    zip_file='zip-test-files/test.zip'
    resp = {}
    test_url='http://connection.error.test'
    exception = requests.exceptions.ConnectionError(test_url)
    responses.add(responses.POST, test_url, body=exception)
    with pytest.raises(requests.HTTPError) as excinfo:
        resp = deploy_sys._request_post_file(test_url, zip_file)
    assert 'Could not connect to URL' in str(excinfo.value)

    test_url='http://invalid.url.test:8081'
    exception = requests.exceptions.InvalidURL(test_url)
    responses.add(responses.POST, test_url, body=exception)
    with pytest.raises(requests.HTTPError) as excinfo:
        resp = deploy_sys._request_post_file(test_url, zip_file)
    assert 'Invalid URL' in str(excinfo.value)

    test_url='http://missing.schema.test:8081'
    exception = requests.exceptions.MissingSchema(test_url)
    responses.add(responses.POST, test_url, body=exception)
    with pytest.raises(requests.HTTPError) as excinfo:
        resp = deploy_sys._request_post_file(test_url, zip_file)
    assert 'Not valid URL' in str(excinfo.value)

    test_url='http://repository.read.only:8081'
    responses.add(responses.POST, test_url, body=None, status=400)
    with pytest.raises(requests.HTTPError) as excinfo:
        resp = deploy_sys._request_post_file(test_url, zip_file)
    assert 'Repository is read only' in str(excinfo.value)

    test_url='http://repository.not.found:8081'
    responses.add(responses.POST, test_url, body=None, status=404)
    with pytest.raises(requests.HTTPError) as excinfo:
        resp = deploy_sys._request_post_file(test_url, zip_file)
    assert 'Did not find repository' in str(excinfo.value)

    test_url='http://other.upload.error:8081'
    responses.add(responses.POST, test_url, body=None, status=500)
    with pytest.raises(requests.HTTPError) as excinfo:
        resp = deploy_sys._request_post_file(test_url, zip_file)
    assert 'Failed to upload to Nexus with status code' in str(excinfo.value)


def test__request_post_file_data(responses, mocker):
    """Test _request_post_file."""

    param={'r':(None, 'testing')}
    zip_file='zip-test-files/test.zip'
    resp = {}
    test_url='http://connection.error.test'
    exception = requests.exceptions.ConnectionError(test_url)
    responses.add(responses.POST, test_url, body=exception)
    with pytest.raises(requests.HTTPError) as excinfo:
        resp = deploy_sys._request_post_file(test_url, zip_file, param)
    assert 'Could not connect to URL' in str(excinfo.value)

    test_url='http://invalid.url.test:8081'
    exception = requests.exceptions.InvalidURL(test_url)
    responses.add(responses.POST, test_url, body=exception)
    with pytest.raises(requests.HTTPError) as excinfo:
        resp = deploy_sys._request_post_file(test_url, zip_file, param)
    assert 'Invalid URL' in str(excinfo.value)

    test_url='http://missing.schema.test:8081'
    exception = requests.exceptions.MissingSchema(test_url)
    responses.add(responses.POST, test_url, body=exception)
    with pytest.raises(requests.HTTPError) as excinfo:
        resp = deploy_sys._request_post_file(test_url, zip_file, param)
    assert 'Not valid URL' in str(excinfo.value)

    test_url='http://repository.read.only:8081'
    responses.add(responses.POST, test_url, body=None, status=400)
    with pytest.raises(requests.HTTPError) as excinfo:
        resp = deploy_sys._request_post_file(test_url, zip_file, param)
    assert 'Repository is read only' in str(excinfo.value)

    test_url='http://repository.not.found:8081'
    responses.add(responses.POST, test_url, body=None, status=404)
    with pytest.raises(requests.HTTPError) as excinfo:
        resp = deploy_sys._request_post_file(test_url, zip_file, param)
    assert 'Did not find repository' in str(excinfo.value)

    test_url='http://other.upload.error:8081'
    responses.add(responses.POST, test_url, body=None, status=500)
    with pytest.raises(requests.HTTPError) as excinfo:
        resp = deploy_sys._request_post_file(test_url, zip_file, param)
    assert 'Failed to upload to Nexus with status code' in str(excinfo.value)


def test_nexus_stage_repo_close(responses, mocker):
    """Test nexus_stage_repo_close."""
    mocker.patch('lftools.deploy._log_error_and_exit', side_effect=mocked_log_error)
    url='service/local/staging/profiles'

    responses.add(responses.POST, 'http://valid.create.post/{}/{}/finish'.format(url, '93fb68073c18' ),
                  body=None, status=201)
    deploy_sys.nexus_stage_repo_close('valid.create.post', '93fb68073c18', 'test1-1027')

    xml_site_not_found = """
        <html><head><title>404 - Site Not Found</title></head>
            <body><h1>404 - Site not found</h1></body>
        </html>
        """
    responses.add(responses.POST, 'http://site.not.found/{}/{}/finish'.format(url, 'INVALID'),
                  body=xml_site_not_found, status=404)
    with pytest.raises(ValueError) as excinfo:
         deploy_sys.nexus_stage_repo_close('site.not.found', 'INVALID', 'test1-1027')
    assert 'site.not.found' in str(excinfo.value)

    xml_missing_staging_repository = """
        <nexus-error><errors><error>
            <id>*</id>
            <msg>Unhandled: Missing staging repository: test1-1</msg>
        </error></errors></nexus-error>
        """
    responses.add(responses.POST, 'http://missing.staging.repository/{}/{}/finish'.format(url, 'INVALID'),
                  body=xml_missing_staging_repository, status=500)
    with pytest.raises(ValueError) as excinfo:
         deploy_sys.nexus_stage_repo_close('missing.staging.repository', 'INVALID', 'test1-1027')
    assert 'missing.staging.repository' in str(excinfo.value)

    xml_staging_already_closed = """
        <nexus-error><errors><error>
            <id>*</id>
            <msg>Unhandled: Repository: test1-1000 has invalid state: closed</msg>
        </error></errors></nexus-error>
        """
    responses.add(responses.POST, 'http://staging.already.closed/{}/{}/finish'.format(url, 'INVALID'),
                  body=xml_staging_already_closed, status=500)
    with pytest.raises(ValueError) as excinfo:
        deploy_sys.nexus_stage_repo_close('staging.already.closed', 'INVALID',  'test1-1027')
    assert 'staging.already.closed' in str(excinfo.value)

    xml_other_error_occured = """
        <html><head><title>303 - See Other</title></head>
            <body><h1>303 - See Other</h1></body>
        </html>
        """
    responses.add(responses.POST, 'http://other.error.occured/{}/{}/finish'.format(url, 'INVALID'),
                  body=xml_other_error_occured, status=303)
    with pytest.raises(ValueError) as excinfo:
        deploy_sys.nexus_stage_repo_close('other.error.occured', 'INVALID', 'test1-1027')
    assert 'other.error.occured' in str(excinfo.value)


def test_nexus_stage_repo_create(responses, mocker):
    """Test nexus_stage_repo_create."""
    mocker.patch('lftools.deploy._log_error_and_exit', side_effect=mocked_log_error)
    url = 'service/local/staging/profiles'

    xml_created = "<stagedRepositoryId>test1-1030</stagedRepositoryId>"
    responses.add(responses.POST, 'http://valid.create.post/{}/{}/start'.format(url, '93fb68073c18' ),
                  body=xml_created, status=201)
    res = deploy_sys.nexus_stage_repo_create('valid.create.post', '93fb68073c18')
    assert res == 'test1-1030'

    xml_profile_id_dont_exist = """
        <nexus-error><errors><error>
            <id>*</id>
            <msg>Cannot create Staging Repository, profile with id &apos;INVALID&apos; does not exist.</msg>
        </error></errors></nexus-error>
        """
    responses.add(responses.POST, 'http://profile.id_not.exist/{}/{}/start'.format(url, 'INVALID' ),
                  body=xml_profile_id_dont_exist, status=404)
    with pytest.raises(ValueError) as excinfo:
        res = deploy_sys.nexus_stage_repo_create('profile.id_not.exist', 'INVALID')
    assert 'profile.id.not.exist' in str(excinfo.value)

    xml_other_create_error = "<nexus-error><errors><error><id>*</id><msg>OTHER create error.</msg></error></errors></nexus-error>"
    responses.add(responses.POST, 'http://other.create.error/{}/{}/start'.format(url, 'INVALID' ),
                  body=xml_other_create_error, status=404)
    with pytest.raises(ValueError) as excinfo:
        res = deploy_sys.nexus_stage_repo_create('other.create.error', 'INVALID')
    assert 'other.create.error' in str(excinfo.value)

    xml_other_error_occured = """
        <html>
            <head><title>303 - See Other</title></head>
            <body><h1>303 - See Other</h1></body>
        </html>
        """
    responses.add(responses.POST, 'http://other.error.occured/{}/{}/start'.format(url, 'INVALID' ),
                  body=xml_other_error_occured, status=303)
    with pytest.raises(ValueError) as excinfo:
        res = deploy_sys.nexus_stage_repo_create('other.error.occured', 'INVALID')
    assert 'other.error.occured' in str(excinfo.value)

    xml_post_not_supported = """
        <html>
            <head>
                <title>405 - HTTP method POST is not supported by this URL</title>
                <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
                <link rel="icon" type="image/png" href="http://192.168.1.26:8081/nexus/favicon.png">
                <!--[if IE]>
                <link rel="SHORTCUT ICON" href="http://192.168.1.26:8081/nexus/favicon.ico"/>
                <![endif]-->
                <link rel="stylesheet" href="http://192.168.1.26:8081/nexus/static/css/Sonatype-content.css?2.14.10-01" type="text/css" media="screen" title="no title" charset="utf-8">
            </head>
            <body>
                <h1>405 - HTTP method POST is not supported by this URL</h1>
                <p>HTTP method POST is not supported by this URL</p>
            </body>
        </html>
        """
    responses.add(responses.POST, 'http://post.not.supported/{}/{}/start'.format(url, 'INVALID' ),
                  body=xml_post_not_supported, status=405)
    with pytest.raises(ValueError) as excinfo:
         res = deploy_sys.nexus_stage_repo_create('post.not.supported', 'INVALID')
    assert 'post.not.supported' in str(excinfo.value)

    xml_site_not_found = """
        <html><head><title>404 - Site Not Found</title></head>
            <body><h1>404 - Site not found</h1></body>
        </html>
        """
    responses.add(responses.POST, 'http://site.not.found/{}/{}/start'.format(url, 'INVALID' ),
                  body=xml_site_not_found, status=404)
    with pytest.raises(ValueError) as excinfo:
        res = deploy_sys.nexus_stage_repo_create('site.not.found', 'INVALID')
    assert 'site.not.found' in str(excinfo.value)


def test__upload_maven_file_to_nexus(responses, mocker):
    """Test upload_to_nexus."""

    zip_file='zip-test-files/test.tar.xz'
    common_urlpart='service/local/artifact/maven/content'

    nexus_repo_id='testing'
    group_id='com5.test'
    artifact_id='ArtId2'
    version='1.2.7'
    packaging='tar.xz'
    classified=None

    resp = {}

    test_url='http://all.ok.upload:8081'
    responses.add(responses.POST, '{}/{}'.format(test_url, common_urlpart), body=None, status=201)
    resp = deploy_sys.upload_maven_file_to_nexus(test_url, nexus_repo_id, group_id, artifact_id, version, packaging, zip_file)

    xml_other_error = """
        <nexus-error><errors><error>
            <id>*</id>
            <msg>Something went wrong.</msg>
        </error></errors></nexus-error>
        """
    test_url='http://something.went.wrong:8081'
    responses.add(responses.POST, '{}/{}'.format(test_url, common_urlpart), body=xml_other_error, status=405)
    with pytest.raises(requests.HTTPError) as excinfo:
        resp = deploy_sys.upload_maven_file_to_nexus(test_url, nexus_repo_id, group_id, artifact_id, version, packaging, zip_file)
    assert 'Something went wrong' in str(excinfo.value)


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, 'deploy'),
    )
def test_deploy_nexus_snapshot(datafiles, responses):
    """Test deploy_nexus with snapshot.

    This test will send a directory of files to deploy_nexus, which should
    call requests.post once for every valid (=3) file.
    There are two files that should not be uploaded.
    """
    os.chdir(str(datafiles))
    nexus_url = 'http://successfull.nexus.deploy/nexus/content/repositories/releases'
    deploy_dir = 'm2repo'

    # Test success - Snapshot
    snapshot = True
    test_files = ['4.0.3-SNAPSHOT/odlparent-lite-4.0.3-20181120.113136-1.pom',
                  '4.0.3-SNAPSHOT/odlparent-lite-4.0.3-20181120.113136-1.pom.sha1',
                  '4.0.3-SNAPSHOT/odlparent-lite-4.0.3-20181120.113136-1.pom.md5',
                  '4.0.3-SNAPSHOT/maven-metadata.xml',
                  '4.0.3-SNAPSHOT/maven-metadata.xml.md5',
                  '4.0.3-SNAPSHOT/maven-metadata.xml.sha1',
                  'maven-metadata.xml',
                  'maven-metadata.xml.md5',
                  'maven-metadata.xml.sha1']
    for file in test_files:
        success_upload_url = '{}/{}'.format(nexus_url, file)
        responses.add(responses.POST, success_upload_url,
                      status=201)
    deploy_sys.deploy_nexus(nexus_url, deploy_dir, snapshot)


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, 'deploy'),
    )
def test_deploy_nexus_nosnapshot(datafiles, responses):
    """Test deploy_nexus with no snapshot.

    This test will send a directory of files to deploy_nexus, which should
    call requests.post once for every valid (=3) file.
    There are six files that should not be uploaded, and three that should.
    """
    os.chdir(str(datafiles))
    nexus_url = 'http://successfull.nexus.deploy/nexus/content/repositories/releases'
    deploy_dir = 'm2repo'

    # Test success - No Snapshot
    test_files = ['4.0.3-SNAPSHOT/odlparent-lite-4.0.3-20181120.113136-1.pom',
                  '4.0.3-SNAPSHOT/odlparent-lite-4.0.3-20181120.113136-1.pom.sha1',
                  '4.0.3-SNAPSHOT/odlparent-lite-4.0.3-20181120.113136-1.pom.md5']
    for file in test_files:
        success_upload_url = '{}/{}'.format(nexus_url, file)
        responses.add(responses.POST, success_upload_url,
                      status=201)
    deploy_sys.deploy_nexus(nexus_url, deploy_dir)


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, 'deploy'),
    )
def test_nexus_deploy_stage(datafiles, responses):
    """Test nexus_deploy_stage."""
    url='http://valid.deploy.stage'
    url_repo = 'service/local/staging/profiles'
    staging_profile_id='93fb68073c18'
    repo_id='test1-1030'

    #Setup for nexus_stage_repo_create
    xml_created = "<stagedRepositoryId>{}</stagedRepositoryId>".format(repo_id)
    responses.add(responses.POST, '{}/{}/{}/start'.format(url, url_repo, staging_profile_id),
                  body=xml_created, status=201)

    #Setup for deploy_nexus with no snapshot
    os.chdir(str(datafiles))
    nexus_deploy_url = '{}/service/local/staging/deployByRepositoryId/{}'.format(url, repo_id)
    deploy_dir = 'm2repo'
    test_files = ['4.0.3-SNAPSHOT/odlparent-lite-4.0.3-20181120.113136-1.pom',
                  '4.0.3-SNAPSHOT/odlparent-lite-4.0.3-20181120.113136-1.pom.sha1',
                  '4.0.3-SNAPSHOT/odlparent-lite-4.0.3-20181120.113136-1.pom.md5']
    for file in test_files:
        success_upload_url = '{}/{}'.format(nexus_deploy_url, file)
        responses.add(responses.POST, success_upload_url,
                      status=201)

    #Setup for nexus_stage_repo_close
    responses.add(responses.POST, '{}/{}/{}/finish'.format(url, url_repo, staging_profile_id),
                  body=None, status=201)

    #Execute test, should not return anything for successful run.
    deploy_sys.deploy_nexus_stage (url, staging_profile_id, deploy_dir)
