# -*- coding: utf-8 -*-
# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Library of functions for deploying artifacts to Nexus."""

import concurrent.futures
import datetime
import errno
import glob
import gzip
import io
import logging
import math
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

import boto3
import requests
import six
from botocore.exceptions import ClientError
from defusedxml.minidom import parseString

log = logging.getLogger(__name__)
logging.getLogger("botocore").setLevel(logging.CRITICAL)


def _compress_text(dir):
    """Compress all text files in directory."""
    save_dir = os.getcwd()
    os.chdir(dir)

    compress_types = [
        "**/*.html",
        "**/*.log",
        "**/*.txt",
        "**/*.xml",
    ]
    paths = []
    for _type in compress_types:
        search = os.path.join(dir, _type)
        paths.extend(glob.glob(search, recursive=True))

    for _file in paths:
        # glob may follow symlink paths that open can't find
        if os.path.exists(_file):
            log.debug("Compressing file {}".format(_file))
            with open(_file, "rb") as src, gzip.open("{}.gz".format(_file), "wb") as dest:
                shutil.copyfileobj(src, dest)
                os.remove(_file)
        else:
            log.info("Could not open path from glob {}".format(_file))

    os.chdir(save_dir)


def _format_url(url):
    """Ensure url starts with http and trim trailing '/'s."""
    start_pattern = re.compile("^(http|https)://")
    if not start_pattern.match(url):
        url = "http://{}".format(url)

    if url.endswith("/"):
        url = url.rstrip("/")

    return url


def _log_error_and_exit(*msg_list):
    """Print error message, and exit."""
    for msg in msg_list:
        log.error(msg)
    sys.exit(1)


def _request_post(url, data, headers):
    """Execute a request post, return the resp."""
    resp = {}
    try:
        resp = requests.post(url, data=data, headers=headers)
    except requests.exceptions.MissingSchema:
        log.debug("in _request_post. MissingSchema")
        _log_error_and_exit("Not valid URL: {}".format(url))
    except requests.exceptions.ConnectionError:
        log.debug("in _request_post. ConnectionError")
        _log_error_and_exit("Could not connect to URL: {}".format(url))
    except requests.exceptions.InvalidURL:
        log.debug("in _request_post. InvalidURL")
        _log_error_and_exit("Invalid URL: {}".format(url))
    return resp


def _get_filenames_in_zipfile(_zipfile):
    """Return a list with file names."""
    files = zipfile.ZipFile(_zipfile).infolist()
    return [f.filename for f in files]


def _request_post_file(url, file_to_upload, parameters=None):
    """Execute a request post, return the resp."""
    resp = {}
    try:
        upload_file = open(file_to_upload, "rb")
    except FileNotFoundError:
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), file_to_upload)

    files = {"file": upload_file}
    try:
        if parameters:
            resp = requests.post(url, data=parameters, files=files)
        else:
            resp = requests.post(url, data=upload_file.read())
    except requests.exceptions.MissingSchema:
        raise requests.HTTPError("Not valid URL: {}".format(url))
    except requests.exceptions.ConnectionError:
        raise requests.HTTPError("Could not connect to URL: {}".format(url))
    except requests.exceptions.InvalidURL:
        raise requests.HTTPError("Invalid URL: {}".format(url))

    if resp.status_code == 400:
        raise requests.HTTPError("Repository is read only")
    elif resp.status_code == 404:
        raise requests.HTTPError("Did not find repository.")

    if not str(resp.status_code).startswith("20"):
        raise requests.HTTPError(
            "Failed to upload to Nexus with status code: {}.\n{}\n{}".format(
                resp.status_code, resp.text, file_to_upload
            )
        )

    return resp


def _request_put_file(url, file_to_upload, parameters=None):
    """Execute a request put, return the resp."""
    resp = {}
    try:
        upload_file = open(file_to_upload, "rb")
    except FileNotFoundError:
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), file_to_upload)

    files = {"file": upload_file}
    try:
        if parameters:
            resp = requests.put(url, data=parameters, files=files)
        else:
            resp = requests.put(url, data=upload_file)
    except requests.exceptions.MissingSchema:
        raise requests.HTTPError("Not valid URL format. Check for https:// etc..: {}".format(url))
    except requests.exceptions.ConnectTimeout:
        raise requests.HTTPError("Timed out connecting to {}".format(url))
    except requests.exceptions.ReadTimeout:
        raise requests.HTTPError("Timed out waiting for the server to reply ({})".format(url))
    except requests.exceptions.ConnectionError:
        raise requests.HTTPError("A connection error occurred ({})".format(url))
    except requests.exceptions.InvalidURL:
        raise requests.HTTPError("Invalid URL format: {}".format(url))
    except requests.RequestException as e:
        log.error(e)

    if resp.status_code == 201:
        return True
    if resp.status_code == 400:
        raise requests.HTTPError("Repository is read only")
    if resp.status_code == 401:
        raise requests.HTTPError("Invalid repository credentials")
    if resp.status_code == 404:
        raise requests.HTTPError("Did not find repository.")

    if not str(resp.status_code).startswith("20"):
        raise requests.HTTPError(
            "Failed to upload to Nexus with status code: {}.\n{}\n{}".format(
                resp.status_code, resp.text, file_to_upload
            )
        )


def _get_node_from_xml(xml_data, tag_name):
    """Extract tag data from xml data."""
    log.debug("xml={}".format(xml_data))

    try:
        dom1 = parseString(xml_data)
        childnode = dom1.getElementsByTagName(tag_name)[0]
    except Exception:
        _log_error_and_exit("Received bad XML, can not find tag {}".format(tag_name), xml_data)
    return childnode.firstChild.data


def _remove_duplicates_and_sort(lst):
    # Remove duplicates from list, and sort it
    no_dups_lst = list(dict.fromkeys(lst))
    no_dups_lst.sort()

    duplicated_list = []
    for i in range(len(no_dups_lst)):
        if lst.count(no_dups_lst[i]) > 1:
            duplicated_list.append(no_dups_lst[i])
    log.debug("duplicates  : {}".format(duplicated_list))

    return no_dups_lst


def copy_archives(workspace, pattern=None):
    """Copy files matching PATTERN in a WORKSPACE to the current directory.

    The best way to use this function is to cd into the directory you wish to
    store the files first before calling the function.

    This function provides 2 ways to archive files:

        1) copy $WORKSPACE/archives directory
        2) copy globstar pattern

    :params:

        :arg str pattern: Space-separated list of Unix style glob patterns.
            (default: None)
    """
    archives_dir = os.path.join(workspace, "archives")
    dest_dir = os.getcwd()

    log.debug("Copying files from {} with pattern '{}' to {}.".format(workspace, pattern, dest_dir))
    log.debug("archives_dir = {}".format(archives_dir))

    if os.path.exists(archives_dir):
        if os.path.isfile(archives_dir):
            log.error("Archives {} is a file, not a directory.".format(archives_dir))
            raise OSError(errno.ENOENT, "Not a directory", archives_dir)
        else:
            log.debug("Archives dir {} does exist.".format(archives_dir))
            for file_or_dir in os.listdir(archives_dir):
                f = os.path.join(archives_dir, file_or_dir)
                try:
                    log.debug("Moving {}".format(f))
                    shutil.move(f, dest_dir)
                except shutil.Error as e:
                    log.error(e)
                    raise OSError(errno.EPERM, "Could not move to", archives_dir)
    else:
        log.error("Archives dir {} does not exist.".format(archives_dir))
        raise OSError(errno.ENOENT, "Missing directory", archives_dir)

    if pattern is None:
        return

    no_dups_pattern = _remove_duplicates_and_sort(pattern)

    paths = []
    for p in no_dups_pattern:
        if p == "":  # Skip empty patterns as they are invalid
            continue

        search = os.path.join(workspace, p)
        paths.extend(glob.glob(search, recursive=True))
    log.debug("Files found: {}".format(paths))

    no_dups_paths = _remove_duplicates_and_sort(paths)
    for src in no_dups_paths:
        if len(os.path.basename(src)) > 255:
            log.warn("Filename {} is over 255 characters. Skipping...".format(os.path.basename(src)))

        dest = os.path.join(dest_dir, src[len(workspace) + 1 :])
        log.debug("{} -> {}".format(src, dest))

        if os.path.isfile(src):
            try:
                shutil.move(src, dest)
            except IOError as e:  # Switch to FileNotFoundError when Python 2 support is dropped.
                log.debug("Missing path, will create it {}.\n{}".format(os.path.dirname(dest), e))
                os.makedirs(os.path.dirname(dest))
                shutil.move(src, dest)
        else:
            log.info("Not copying directories: {}.".format(src))

    # Create a temp file to handle empty dirs in AWS S3 buckets.
    if os.environ.get("S3_BUCKET") is not None:
        now = datetime.datetime.now()
        p = now.strftime("_%d%m%Y_%H%M%S_")
        for dirpath, dirnames, files in os.walk(dest_dir):
            if not files:
                fd, tmp = tempfile.mkstemp(prefix=p, dir=dirpath)
                os.close(fd)
                log.debug("temp file created in dir: {}.".format(dirpath))


def deploy_archives(nexus_url, nexus_path, workspace, pattern=None):
    """Archive files to a Nexus site repository named logs.

    Provides 2 ways to archive files:
        1) $WORKSPACE/archives directory provided by the user.
        2) globstar pattern provided by the user.

    Requirements:

    To use this API a Nexus server must have a site repository configured
    with the name "logs" as this is a hardcoded path.

    Parameters:

        :nexus_url: URL of Nexus server. Eg: https://nexus.opendaylight.org
        :nexus_path: Path on nexus logs repo to place the logs. Eg:
            $SILO/$JENKINS_HOSTNAME/$JOB_NAME/$BUILD_NUMBER
        :workspace: Directory in which to search, typically in Jenkins this is
            $WORKSPACE
        :pattern: Space-separated list of Globstar patterns of files to
            archive. (optional)
    """
    nexus_url = _format_url(nexus_url)
    previous_dir = os.getcwd()
    work_dir = tempfile.mkdtemp(prefix="lftools-da.")
    os.chdir(work_dir)
    log.debug("workspace: {}, work_dir: {}".format(workspace, work_dir))

    copy_archives(workspace, pattern)
    _compress_text(work_dir)

    archives_zip = shutil.make_archive("{}/archives".format(workspace), "zip")
    log.debug("archives zip: {}".format(archives_zip))
    deploy_nexus_zip(nexus_url, "logs", nexus_path, archives_zip)

    os.chdir(previous_dir)
    shutil.rmtree(work_dir)


def deploy_logs(nexus_url, nexus_path, build_url):
    """Deploy logs to a Nexus site repository named logs.

    Fetches logs and system information and pushes them to Nexus
    for log archiving.
    Requirements:

    To use this API a Nexus server must have a site repository configured
    with the name "logs" as this is a hardcoded path.

    Parameters:

        :nexus_url: URL of Nexus server. Eg: https://nexus.opendaylight.org
        :nexus_path: Path on nexus logs repo to place the logs. Eg:
            $SILO/$JENKINS_HOSTNAME/$JOB_NAME/$BUILD_NUMBER
        :build_url: URL of the Jenkins build. Jenkins typically provides this
                    via the $BUILD_URL environment variable.
    """
    nexus_url = _format_url(nexus_url)
    previous_dir = os.getcwd()
    work_dir = tempfile.mkdtemp(prefix="lftools-dl.")
    os.chdir(work_dir)
    log.debug("work_dir: {}".format(work_dir))

    build_details = open("_build-details.log", "w+")
    build_details.write("build-url: {}".format(build_url))

    with open("_sys-info.log", "w+") as sysinfo_log:
        sys_cmds = []

        log.debug("Platform: {}".format(sys.platform))
        if sys.platform == "linux" or sys.platform == "linux2":
            sys_cmds = [
                ["uname", "-a"],
                ["lscpu"],
                ["nproc"],
                ["df", "-h"],
                ["free", "-m"],
                ["ip", "addr"],
                ["sar", "-b", "-r", "-n", "DEV"],
                ["sar", "-P", "ALL"],
            ]

        for c in sys_cmds:
            try:
                output = subprocess.check_output(c).decode("utf-8")
            except OSError:  # TODO: Switch to FileNotFoundError when Python < 3.5 support is dropped.
                log.debug("Command not found: {}".format(c))
                continue

            output = "---> {}:\n{}\n".format(" ".join(c), output)
            sysinfo_log.write(output)
            log.info(output)

    build_details.close()

    # Magic string used to trim console logs at the appropriate level during wget
    MAGIC_STRING = "-----END_OF_BUILD-----"
    log.info(MAGIC_STRING)

    resp = requests.get("{}/consoleText".format(_format_url(build_url)))
    with io.open("console.log", "w+", encoding="utf-8") as f:
        f.write(six.text_type(resp.content.decode("utf-8").split(MAGIC_STRING)[0]))

    resp = requests.get("{}/timestamps?time=HH:mm:ss&appendLog".format(_format_url(build_url)))
    with io.open("console-timestamp.log", "w+", encoding="utf-8") as f:
        f.write(six.text_type(resp.content.decode("utf-8").split(MAGIC_STRING)[0]))

    _compress_text(work_dir)

    console_zip = tempfile.NamedTemporaryFile(prefix="lftools-dl", delete=True)
    log.debug("console-zip: {}".format(console_zip.name))
    shutil.make_archive(console_zip.name, "zip", work_dir)
    deploy_nexus_zip(nexus_url, "logs", nexus_path, "{}.zip".format(console_zip.name))
    console_zip.close()

    os.chdir(previous_dir)
    shutil.rmtree(work_dir)


def deploy_s3(s3_bucket, s3_path, build_url, workspace, pattern=None):
    """Add logs and archives to temp directory to be shipped to S3 bucket.

    Fetches logs and system information and pushes them and archives to S3
    for log archiving.

    Requires the s3 bucket to exist.

    Parameters:

        :s3_bucket: Name of S3 bucket. Eg: lf-project-date
        :s3_path: Path on S3 bucket place the logs and archives. Eg:
            $SILO/$JENKINS_HOSTNAME/$JOB_NAME/$BUILD_NUMBER
        :build_url: URL of the Jenkins build. Jenkins typically provides this
                    via the $BUILD_URL environment variable.
        :workspace: Directory in which to search, typically in Jenkins this is
            $WORKSPACE
        :pattern: Space-separated list of Globstar patterns of files to
            archive. (optional)
    """

    def _upload_to_s3(file):
        extra_args = {"ContentType": "text/plain"}
        text_html_extra_args = {"ContentType": "text/html", "ContentEncoding": mimetypes.guess_type(file)[1]}
        text_plain_extra_args = {"ContentType": "text/plain", "ContentEncoding": mimetypes.guess_type(file)[1]}
        app_xml_extra_args = {"ContentType": "application/xml", "ContentEncoding": mimetypes.guess_type(file)[1]}
        if file == "_tmpfile":
            for dir in (logs_dir, silo_dir, jenkins_node_dir):
                try:
                    s3.Bucket(s3_bucket).upload_file(file, "{}{}".format(dir, file))
                except ClientError as e:
                    log.error(e)
                    return False
                return True
        if mimetypes.guess_type(file)[0] is None and mimetypes.guess_type(file)[1] is None:
            try:
                s3.Bucket(s3_bucket).upload_file(file, "{}{}".format(s3_path, file), ExtraArgs=extra_args)
            except ClientError as e:
                log.error(e)
                return False
            return True
        elif mimetypes.guess_type(file)[0] is None or mimetypes.guess_type(file)[0] in "text/plain":
            extra_args = text_plain_extra_args
            try:
                s3.Bucket(s3_bucket).upload_file(file, "{}{}".format(s3_path, file), ExtraArgs=extra_args)
            except ClientError as e:
                log.error(e)
                return False
            return True
        elif mimetypes.guess_type(file)[0] in "text/html":
            extra_args = text_html_extra_args
            try:
                s3.Bucket(s3_bucket).upload_file(file, "{}{}".format(s3_path, file), ExtraArgs=extra_args)
            except ClientError as e:
                log.error(e)
                return False
            return True
        elif mimetypes.guess_type(file)[0] in "application/xml":
            extra_args = app_xml_extra_args
            try:
                s3.Bucket(s3_bucket).upload_file(file, "{}{}".format(s3_path, file), ExtraArgs=extra_args)
            except ClientError as e:
                log.error(e)
                return False
            return True
        else:
            try:
                s3.Bucket(s3_bucket).upload_file(file, "{}{}".format(s3_path, file), ExtraArgs=extra_args)
            except ClientError as e:
                log.error(e)
                return False
            return True

    previous_dir = os.getcwd()
    work_dir = tempfile.mkdtemp(prefix="lftools-dl.")
    os.chdir(work_dir)
    s3_bucket = s3_bucket.lower()
    s3 = boto3.resource("s3")
    logs_dir = s3_path.split("/")[0] + "/"
    silo_dir = s3_path.split("/")[1] + "/"
    jenkins_node_dir = logs_dir + silo_dir + s3_path.split("/")[2] + "/"

    log.debug("work_dir: {}".format(work_dir))

    # Copy archive files to tmp dir
    copy_archives(workspace, pattern)

    # Create build logs
    build_details = open("_build-details.log", "w+")
    build_details.write("build-url: {}".format(build_url))

    with open("_sys-info.log", "w+") as sysinfo_log:
        sys_cmds = []

        log.debug("Platform: {}".format(sys.platform))
        if sys.platform == "linux" or sys.platform == "linux2":
            sys_cmds = [
                ["uname", "-a"],
                ["lscpu"],
                ["nproc"],
                ["df", "-h"],
                ["free", "-m"],
                ["ip", "addr"],
                ["sar", "-b", "-r", "-n", "DEV"],
                ["sar", "-P", "ALL"],
            ]

        for c in sys_cmds:
            try:
                output = subprocess.check_output(c).decode("utf-8")
            except FileNotFoundError:
                log.debug("Command not found: {}".format(c))
                continue

            output = "---> {}:\n{}\n".format(" ".join(c), output)
            sysinfo_log.write(output)
            log.info(output)

    build_details.close()
    sysinfo_log.close()

    # Magic string used to trim console logs at the appropriate level during wget
    MAGIC_STRING = "-----END_OF_BUILD-----"
    log.info(MAGIC_STRING)

    resp = requests.get("{}/consoleText".format(_format_url(build_url)))
    with open("console.log", "w+", encoding="utf-8") as f:
        f.write(six.text_type(resp.content.decode("utf-8").split(MAGIC_STRING)[0]))
        f.close()

    resp = requests.get("{}/timestamps?time=HH:mm:ss&appendLog".format(_format_url(build_url)))
    with open("console-timestamp.log", "w+", encoding="utf-8") as f:
        f.write(six.text_type(resp.content.decode("utf-8").split(MAGIC_STRING)[0]))
        f.close()

    # Create _tmpfile
    """ Because s3 does not have a filesystem, this file is uploaded to generate/update the
        index.html file in the top level "directories". """
    open("_tmpfile", "a").close()

    # Compress tmp directory
    _compress_text(work_dir)

    # Create file list to upload
    file_list = []
    files = glob.glob("**/*", recursive=True)
    for file in files:
        if os.path.isfile(file):
            file_list.append(file)

    log.info("#######################################################")
    log.info("Deploying files from {} to {}/{}".format(work_dir, s3_bucket, s3_path))

    # Perform s3 upload
    for file in file_list:
        log.info("Attempting to upload file {}".format(file))
        if _upload_to_s3(file):
            log.info("Successfully uploaded {}".format(file))
        else:
            log.error("FAILURE: Uploading {} failed".format(file))

    log.info("Finished deploying from {} to {}/{}".format(work_dir, s3_bucket, s3_path))
    log.info("#######################################################")

    # Cleanup
    s3.Object(s3_bucket, "{}{}".format(logs_dir, "_tmpfile")).delete()
    s3.Object(s3_bucket, "{}{}".format(silo_dir, "_tmpfile")).delete()
    s3.Object(s3_bucket, "{}{}".format(jenkins_node_dir, "_tmpfile")).delete()
    os.chdir(previous_dir)
    # shutil.rmtree(work_dir)


def deploy_nexus_zip(nexus_url, nexus_repo, nexus_path, zip_file):
    """"Deploy zip file containing artifacts to Nexus using requests.

    This function simply takes a zip file preformatted in the correct
    directory for Nexus and uploads to a specified Nexus repo using the
    content-compressed URL.

    Requires the Nexus Unpack plugin and permission assigned to the upload user.

    Parameters:

        nexus_url:    URL to Nexus server. (Ex: https://nexus.opendaylight.org)
        nexus_repo:   The repository to push to. (Ex: site)
        nexus_path:   The path to upload the artifacts to. Typically the
                      project group_id depending on if a Maven or Site repo
                      is being pushed.
                      Maven Ex: org/opendaylight/odlparent
                      Site Ex: org.opendaylight.odlparent
        zip_file:     The zip to deploy. (Ex: /tmp/artifacts.zip)

    Sample:
    lftools deploy nexus-zip \
        192.168.1.26:8081/nexus \
        snapshots \
        tst_path \
        tests/fixtures/deploy/zip-test-files/test.zip
    """
    url = "{}/service/local/repositories/{}/content-compressed/{}".format(
        _format_url(nexus_url), nexus_repo, nexus_path
    )
    log.debug("Uploading {} to {}".format(zip_file, url))

    try:
        resp = _request_post_file(url, zip_file)
    except requests.HTTPError as e:
        files = _get_filenames_in_zipfile(zip_file)
        log.info("Uploading {} failed. It contained the following files".format(zip_file))
        for f in files:
            log.info("   {}".format(f))
        raise requests.HTTPError(e)
    log.debug("{}: {}".format(resp.status_code, resp.text))


def nexus_stage_repo_create(nexus_url, staging_profile_id):
    """Create a Nexus staging repo.

    Parameters:
    nexus_url:           URL to Nexus server. (Ex: https://nexus.example.org)
    staging_profile_id:  The staging profile id as defined in Nexus for the
                         staging repo.

    Returns:             staging_repo_id

    Sample:
    lftools deploy nexus-stage-repo-create 192.168.1.26:8081/nexus/ 93fb68073c18
    """
    nexus_url = "{0}/service/local/staging/profiles/{1}/start".format(_format_url(nexus_url), staging_profile_id)

    log.debug("Nexus URL           = {}".format(nexus_url))

    xml = """
        <promoteRequest>
            <data>
                <description>Create staging repository.</description>
            </data>
        </promoteRequest>
    """

    headers = {"Content-Type": "application/xml"}
    resp = _request_post(nexus_url, xml, headers)

    log.debug("resp.status_code = {}".format(resp.status_code))
    log.debug("resp.text = {}".format(resp.text))

    if re.search("nexus-error", resp.text):
        error_msg = _get_node_from_xml(resp.text, "msg")
        if re.search(".*profile with id:.*does not exist.", error_msg):
            _log_error_and_exit("Staging profile id {} not found.".format(staging_profile_id))
        _log_error_and_exit(error_msg)

    if resp.status_code == 405:
        _log_error_and_exit("HTTP method POST is not supported by this URL", nexus_url)
    if resp.status_code == 404:
        _log_error_and_exit("Did not find nexus site: {}".format(nexus_url))
    if not resp.status_code == 201:
        _log_error_and_exit("Failed with status code {}".format(resp.status_code), resp.text)

    staging_repo_id = _get_node_from_xml(resp.text, "stagedRepositoryId")
    log.debug("staging_repo_id = {}".format(staging_repo_id))

    return staging_repo_id


def nexus_stage_repo_close(nexus_url, staging_profile_id, staging_repo_id):
    """Close a Nexus staging repo.

    Parameters:
    nexus_url:          URL to Nexus server. (Ex: https://nexus.example.org)
    staging_profile_id: The staging profile id as defined in Nexus for the
                        staging repo.
    staging_repo_id:    The ID of the repo to close.

    Sample:
    lftools deploy nexus-stage-repo-close 192.168.1.26:8081/nexsus/ 93fb68073c18 test1-1031
    """
    nexus_url = "{0}/service/local/staging/profiles/{1}/finish".format(_format_url(nexus_url), staging_profile_id)

    log.debug("Nexus URL           = {}".format(nexus_url))
    log.debug("staging_repo_id     = {}".format(staging_repo_id))

    xml = """
        <promoteRequest>
            <data>
                <stagedRepositoryId>{0}</stagedRepositoryId>
                <description>Close staging repository.</description>
            </data>
        </promoteRequest>
    """.format(
        staging_repo_id
    )

    headers = {"Content-Type": "application/xml"}
    resp = _request_post(nexus_url, xml, headers)

    log.debug("resp.status_code = {}".format(resp.status_code))
    log.debug("resp.text = {}".format(resp.text))

    if re.search("nexus-error", resp.text):
        error_msg = _get_node_from_xml(resp.text, "msg")
    else:
        error_msg = resp.text

    if resp.status_code == 404:
        _log_error_and_exit("Did not find nexus site: {}".format(nexus_url))

    if re.search("invalid state: closed", error_msg):
        _log_error_and_exit("Staging repository is already closed.")
    if re.search("Missing staging repository:", error_msg):
        _log_error_and_exit("Staging repository do not exist.")

    if not resp.status_code == 201:
        _log_error_and_exit("Failed with status code {}".format(resp.status_code), resp.text)


def upload_maven_file_to_nexus(
    nexus_url, nexus_repo_id, group_id, artifact_id, version, packaging, file, classifier=None
):
    """Upload file to Nexus as a Maven artifact.

    This function will upload an artifact to Nexus while providing all of
    the usual Maven pom.xml information so that it conforms to Maven 2 repo
    specs.

    Parameters:
         nexus_url:     The URL to the Nexus repo.
                        (Ex:  https://nexus.example.org)
         nexus_repo_id: Repo ID of repo to push artifact to.
         group_id:      Maven style Group ID to upload artifact as.
         artifact_id:   Maven style Artifact ID to upload artifact as.
         version:       Maven style Version to upload artifact as.
         packaging:     Packaging type to upload as (Eg. tar.xz)
         file:          File to upload.
         classifier:    Maven classifier. (optional)

    Sample:
        lftools deploy nexus \
            http://192.168.1.26:8081/nexus/content/repositories/releases \
            tests/fixtures/deploy/zip-test-files
    """
    url = "{}/service/local/artifact/maven/content".format(_format_url(nexus_url))

    log.info("Uploading URL: {}".format(url))
    params = {}
    params.update({"r": (None, "{}".format(nexus_repo_id))})
    params.update({"g": (None, "{}".format(group_id))})
    params.update({"a": (None, "{}".format(artifact_id))})
    params.update({"v": (None, "{}".format(version))})
    params.update({"p": (None, "{}".format(packaging))})
    if classifier:
        params.update({"c": (None, "{}".format(classifier))})

    log.debug("Maven Parameters: {}".format(params))

    resp = _request_post_file(url, file, params)

    if re.search("nexus-error", resp.text):
        error_msg = _get_node_from_xml(resp.text, "msg")
        raise requests.HTTPError("Nexus Error: {}".format(error_msg))


def deploy_nexus(nexus_repo_url, deploy_dir, snapshot=False, workers=2):
    """Deploy a local directory of files to a Nexus repository.

    One purpose of this is so that we can get around the problematic
    deploy-at-end configuration with upstream Maven.
    https://issues.apache.org/jira/browse/MDEPLOY-193

    This function ignores these files:

        - _remote.repositories
        - resolver-status.properties
        - maven-metadata.xml*  (if not a snapshot repo)

    Parameters:
        nexus_repo_url: URL to Nexus repository to upload to.
                        (Ex: https://nexus.example.org/content/repositories/releases)
        deploy_dir:     The directory to deploy. (Ex: /tmp/m2repo)

    Sample:
        lftools deploy nexus \
            http://192.168.1.26:8081/nexus/content/repositories/releases \
            tests/fixtures/deploy/zip-test-files
    """

    def _get_filesize(file):
        bytesize = os.path.getsize(file)
        if bytesize == 0:
            return "0B"
        suffix = ("b", "kb", "mb", "gb")
        i = int(math.floor(math.log(bytesize, 1024)))
        p = math.pow(1024, i)
        s = round(bytesize / p, 2)
        return "{} {}".format(s, suffix[i])

    def _deploy_nexus_upload(file):
        # Fix file path, and call _request_put_file.
        nexus_url_with_file = "{}/{}".format(_format_url(nexus_repo_url), file)
        log.info("Attempting to upload {} ({})".format(file, _get_filesize(file)))
        if _request_put_file(nexus_url_with_file, file):
            return True
        else:
            return False

    file_list = []
    previous_dir = os.getcwd()
    os.chdir(deploy_dir)
    files = glob.glob("**/*", recursive=True)
    for file in files:
        if os.path.isfile(file):
            base_name = os.path.basename(file)

            # Skip blacklisted files
            if base_name == "_remote.repositories" or base_name == "resolver-status.properties":
                continue

            if not snapshot:
                if base_name.startswith("maven-metadata.xml"):
                    continue

            file_list.append(file)

    log.info("#######################################################")
    log.info("Deploying directory {} to {}".format(deploy_dir, nexus_repo_url))

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        # this creates a dict where the key is the Future object, and the value is the file name
        # see concurrent.futures.Future for more info
        futures = {executor.submit(_deploy_nexus_upload, file_name): file_name for file_name in file_list}
        for future in concurrent.futures.as_completed(futures):
            filename = futures[future]
            try:
                data = future.result()
                # remove pyflake warning
                if data == data:
                    pass
            except Exception as e:
                log.error("Uploading {}: {}".format(filename, e))

        # wait until all threads complete (successfully or not)
        # then log the results of the upload threads
        concurrent.futures.wait(futures)
        for k, v in futures.items():
            if k.result():
                log.info("Successfully uploaded {}".format(v))
            else:
                log.error("FAILURE: Uploading {} failed".format(v))

    log.info("Finished deploying {} to {}".format(deploy_dir, nexus_repo_url))
    log.info("#######################################################")

    os.chdir(previous_dir)


def deploy_nexus_stage(nexus_url, staging_profile_id, deploy_dir):
    """Deploy Maven artifacts to Nexus staging repo.

    Parameters:
    nexus_url:          URL to Nexus server. (Ex: https://nexus.example.org)
    staging_profile_id: The staging profile id as defined in Nexus for the
                        staging repo.
    deploy_dir:         The directory to deploy. (Ex: /tmp/m2repo)

    # Sample:
        lftools deploy nexus-stage http://192.168.1.26:8081/nexus 4e6f95cd2344 /tmp/slask
            Deploying Maven artifacts to staging repo...
            Staging repository aaf-1005 created.
            /tmp/slask ~/LF/work/lftools-dev/lftools/shell
            Uploading fstab
            Uploading passwd
            ~/LF/work/lftools-dev/lftools/shell
            Completed uploading files to aaf-1005.
    """
    staging_repo_id = nexus_stage_repo_create(nexus_url, staging_profile_id)
    log.info("Staging repository {} created.".format(staging_repo_id))

    deploy_nexus_url = "{0}/service/local/staging/deployByRepositoryId/{1}".format(
        _format_url(nexus_url), staging_repo_id
    )

    sz_m2repo = sum(os.path.getsize(f) for f in os.listdir(deploy_dir) if os.path.isfile(f))
    log.debug("Staging repository upload size: {} bytes".format(sz_m2repo))

    log.debug("Nexus Staging URL: {}".format(_format_url(deploy_nexus_url)))
    deploy_nexus(deploy_nexus_url, deploy_dir)

    nexus_stage_repo_close(nexus_url, staging_profile_id, staging_repo_id)
    log.info("Completed uploading files to {}.".format(staging_repo_id))
