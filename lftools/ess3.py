import concurrent
import glob
import mimetypes
import os
import shutil
import subprocess
import sys
import tempfile

import boto3
import requests
from botocore.exceptions import ClientError
import logging

from lftools.deploy import copy_archives, _compress_text, _format_url

log = logging.getLogger(__name__)


def deploy_s3(s3_bucket, s3_path, build_url, workspace, pattern=None):
    """Add logs and archives to temp directory to be shipped to S3 bucket.

    Fetches logs and system information and pushes them and archives to S3
    for log archiving.

    Requires the s3 bucket to exist.

    :param s3_bucket: Name of S3 bucket. Eg: lf-project-date
    :param s3_path: Path on S3 bucket place the logs and archives. Eg:
        $SILO/$JENKINS_HOSTNAME/$JOB_NAME/$BUILD_NUMBER
    :param build_url: URL of the Jenkins build. Jenkins typically provides this
                via the $BUILD_URL environment variable.
    :param workspace: Directory in which to search, typically in Jenkins this is
        $WORKSPACE
    :param pattern: Space-separated list of Globstar patterns of files to
        archive. (optional)
    """

    def _s3_upload(s3_path, payload_file, extras=None):
        try:
            if extras:
                s3.Bucket(s3_bucket).upload_file(payload_file, "{}{}".format(s3_path, payload_file), ExtraArgs=extras)
            else:
                s3.Bucket(s3_bucket).upload_file(payload_file, "{}{}".format(s3_path, payload_file))
            return True
        except ClientError as e:
            log.error(e)
            return False

    def _upload(s3_path, payload_file):
        if payload_file in "_tmpfile":
            for _dir in (logs_dir, silo_dir, jenkins_node_dir):
                _s3_upload(s3_path, payload_file)

        if mimetypes.guess_type(file)[0] is None and mimetypes.guess_type(file)[1] is None:
            _s3_upload(s3_path, payload_file, extras={"Content-Type":"octet/stream"})

        if mimetypes.guess_type(file)[0] is None:
            _s3_upload(s3_path, payload_file,
                       extras={"Content-Type": "octet/stream", "Content-Encoding": mimetypes.guess_type(file)[1]})

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
    _compress_text(work_dir)

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
        f.write(r.text.split(MAGIC_STRING)[0])
        f.close()

    resp = requests.get("{}/timestamps?time=HH:mm:ss&appendLog".format(_format_url(build_url)))
    with open("console-timestamp.log", "w+", encoding="utf-8") as f:
        f.write(resp.text.split(MAGIC_STRING)[0])
        f.close()

    log.info("Creating required _tmpfile")
    open("_tmpfile", "a").close()

    _compress_text(work_dir)

    # Create file list to upload
    file_list = []
    files = glob.glob("**/*", recursive=True)
    for file in files:
        if os.path.isfile(file):
            file_list.append(file)

    # Perform async upload
    log.info("#######################################################")
    log.info("Deploying files from {} to {}/{}".format(work_dir, s3_bucket, s3_path))

    for payload_file in file_list:
        _upload(s3_path, payload_file)

    log.info("Finished deploying from {} to {}/{}".format(work_dir, s3_bucket, s3_path))
    log.info("#######################################################")

    # Cleanup
    s3.Object(s3_bucket, "{}{}".format(logs_dir, "_tmpfile")).delete()
    s3.Object(s3_bucket, "{}{}".format(silo_dir, "_tmpfile")).delete()
    s3.Object(s3_bucket, "{}{}".format(jenkins_node_dir, "_tmpfile")).delete()
    os.chdir(previous_dir)
    shutil.rmtree(work_dir)
