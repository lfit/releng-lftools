# -*- coding: utf-8 -*-
# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2018 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Set of functions to facilitate copying nexus3 release images to docker hub.

Workflow if you do it manually

    sudo docker login       ---> DOCKER Credentials
    sudo docker login nexus3.onap.org:10002 -u <yourLFID>

    TAB1 https://nexus3.onap.org/#browse/search=repository_name%3Ddocker.release
    TAB2 https://hub.docker.com/r/onap

    docker pull nexus3.onap.org:10002/onap/aaf/aaf_hello:2.1.3
    docker images --> imageid --> 991170554e6e
    docker tag 991170554e6e onap/aaf-aaf_hello:2.1.3
    docker push onap/aaf-aaf_hello:2.1.3
    docker image rm --force 991170554e6e

Filter
Find all projects that starts with org and contains repo (if specified).

Set the repo to "" to find all projects that starts with org

Set the repo to a str to find all projects that contains that string
  and starts with org
    repo = "aaf_co"   # onap/aaf/aaf_config,onap/aaf/aaf_core
    repo = "aaf_cm"   # onap/aaf/aaf_cm
    repo = "aa"
    repo = ""         # Find all projects

lftools nexus docker releasedockerhub
"""
from __future__ import print_function

import datetime
import json
import logging
import multiprocessing
import os
import re
import shutil
import socket
import tempfile
from multiprocessing.dummy import Pool as ThreadPool
from time import sleep

import boto3
import docker
import requests
import tqdm
import urllib3

log = logging.getLogger(__name__)

NexusCatalog = []
OrigNexusCatalog = []
projects = []
TotTagsToBeCopied = 0

# Dockerhub has started limiting access to
# - 100 requests for anonymous and
# - 200 for non-anonymous access
# This script is using anonymous access to get the dockerhub tags
# and non-anonymous access to do the push.
# States 21600 seconds, but lets give them a bit more
throttling_delay_seconds = 21700
nexus3_batch_size = 70

NEXUS3_BASE = ""
NEXUS3_CATALOG = ""
NEXUS3_PROJ_NAME_HEADER = ""
DOCKER_PROJ_NAME_HEADER = ""
VERSION_REGEXP = ""
DEFAULT_REGEXP = r"^\d+.\d+.\d+$"

local_s3_copy = tempfile.mkdtemp()
lastrun_filename = "{}/last_run_of_release_docker_hub.txt".format(local_s3_copy)
lastnexusrepo_filename = "{}/last_nexus_repo.txt".format(local_s3_copy)

lastrun_format = "%Y-%m-%d %H:%M:%S"
no_timestamp_str = "1901-01-01 01:01:01"
# Default s3 bucket name, if none provided
def_s3_bucket_name = "onap-dockerhub-release-logs-bucket"
USE_S3_BUCKET = True
s3_bucket_name = ""


def _remove_http_from_url(url):
    """Remove http[s]:// from url."""
    if url.startswith("https://"):
        return url[len("https://") :]
    if url.startswith("http://"):
        return url[len("http://") :]
    return url


def _format_image_id(id):
    """Remove sha256: from beginning of string."""
    if id.startswith("sha256:"):
        return id[len("sha256:") :]
    else:
        return id


def _request_get(url):
    """Execute a request get, return the resp."""
    resp = {}
    try:
        resp = requests.get(url)
    except requests.exceptions.RequestException as excinfo:
        log.debug("in _request_get RequestException. {}".format(type(excinfo)))
        raise requests.HTTPError("Issues with URL: {} - {}".format(url, type(excinfo)))
    except socket.gaierror as excinfo:
        log.debug("in _request_get gaierror. {}".format(type(excinfo)))
        raise requests.HTTPError("Issues with URL: {} - {}".format(url, type(excinfo)))
    except requests.exceptions.ConnectionError as excinfo:
        log.debug("in _request_get ConnectionError. {}".format(type(excinfo)))
        raise requests.HTTPError("Issues with URL: {} - {}".format(url, type(excinfo)))
    except urllib3.exceptions.NewConnectionError as excinfo:
        log.debug("in _request_get NewConnectionError. {}".format(type(excinfo)))
        raise requests.HTTPError("Issues with URL: {} - {}".format(url, type(excinfo)))
    except urllib3.exceptions.MaxRetryError as excinfo:
        log.debug("in _request_get MaxRetryError. {}".format(type(excinfo)))
        raise requests.HTTPError("Issues with URL: {} - {}".format(url, type(excinfo)))
    return resp


def which_version_regexp_to_use(input_regexp_or_filename):
    """Set version regexp as per user request.

    regexp is either a regexp to be directly used, or its a file name,
    and the file contains the regexp to use
    """
    global VERSION_REGEXP
    if len(input_regexp_or_filename) == 0:
        VERSION_REGEXP = DEFAULT_REGEXP
    else:
        isFile = os.path.isfile(input_regexp_or_filename)
        if isFile:
            with open(input_regexp_or_filename, "r") as fp:
                VERSION_REGEXP = fp.readline().strip()
        else:
            VERSION_REGEXP = input_regexp_or_filename


def validate_regexp():
    global VERSION_REGEXP
    try:
        re.compile(VERSION_REGEXP)
        is_valid = True
    except re.error:
        is_valid = False
    return is_valid


def initialize(org_name, input_regexp_or_filename=""):
    """Set constant strings."""
    global NEXUS3_BASE
    global NEXUS3_CATALOG
    global NEXUS3_PROJ_NAME_HEADER
    global DOCKER_PROJ_NAME_HEADER
    NEXUS3_BASE = "https://nexus3.{}.org:10002".format(org_name)
    NEXUS3_CATALOG = NEXUS3_BASE + "/v2/_catalog"
    NEXUS3_PROJ_NAME_HEADER = "Nexus3 Project Name"
    DOCKER_PROJ_NAME_HEADER = "Docker HUB Project Name"
    which_version_regexp_to_use(input_regexp_or_filename)


class AnonymousThrottlingStatus:
    def __init__(self):
        """Initialize this class.
        print (resp.headers["ratelimit-remaining"])
        95;w=21600
        print (resp.headers["ratelimit-limit"])
        100;w=21600
        """

        # Get token
        resp = _request_get(
            "https://auth.docker.io/token?service=registry.docker.io&scope=repository:ratelimitpreview/test:pull"
        )
        data = json.loads(resp.text)
        token = data["token"]
        # Use token to get throttle status
        headers = {"Authorization": "Bearer {}".format(token)}
        url = "https://registry-1.docker.io/v2/ratelimitpreview/test/manifests/latest"
        resp = requests.get(url, headers=headers)
        self.limit = resp.headers["ratelimit-limit"].split(";")[0]
        self.remaining = resp.headers["ratelimit-remaining"].split(";")[0]


class TagClass:
    """Base class for Nexus3 and Docker Hub tag class.

    This class contains the actual valid and invalid tags for a repository,
    as well as an indication if the repository exist or not.

    A valid tag has the following format #.#.# (1.2.3, or 1.22.333)

    Parameter:
        org_name  : The organization part of the repository. (onap)
        repo_name : The Nexus3 repository name (aaf/aaf_service)
        repo_from_file : Repository name was taken from input file.
    """

    def __init__(self, org_name, repo_name, repo_from_file):
        """Initialize this class."""
        self.valid = []
        self.invalid = []
        self.repository_exist = True
        self.org = org_name
        self.repo = repo_name
        self.repofromfile = repo_from_file

    def _validate_tag(self, check_tag):
        r"""Local helper function to simplify validity check of version number.

        Returns true or false, depending if the version pattern is a valid one.
        Valid pattern is #.#.#, or in computer term "^\d+.\d+.\d+$"

        Future pattern : x.y.z-KEYWORD-yyyymmddThhmmssZ
          where keyword = STAGING or SNAPSHOT
          '^\d+.\d+.\d+-(STAGING|SNAPSHOT)-(20\d{2})(\d{2})(\d{2})T([01]\d|2[0-3])([0-5]\d)([0-5]\d)Z$'
        """
        pattern = re.compile(r"{}".format(VERSION_REGEXP))
        log.debug("validate tag {} in {} --> {}".format(check_tag, self.repo, pattern.match(check_tag)))
        return pattern.match(check_tag)

    def add_tag(self, new_tag):
        """Add tag to a list.

        This function will take a tag, and add it to the correct list
        (valid or invalid), depending on validate_tag result.
        """
        if self._validate_tag(new_tag):
            self.valid.append(new_tag)
        else:
            self.invalid.append(new_tag)


class NexusTagClass(TagClass):
    """Nexus Tag class.

    This class fetches and stores all Nexus3 tags for a repository.

    Doing this manually from command line, you will give this command:
        curl -s https://nexus3.onap.org:10002/v2/onap/aaf/aaf_service/tags/list
    which gives you the following output:
        {"name":"onap/aaf/aaf_service","tags":["2.1.1","2.1.3","2.1.4","2.1.5","2.1.6","2.1.7","2.1.8"]}
    # https://nexus3.edgexfoundry.org/repository/docker.staging/v2/docker-device-rest-go/tags/list
    # https://nexus3.edgexfoundry.org:10002/v2/docker-device-rest-go/tags/list

    When we fetch the tags from the Nexus3 repository url, they are returned like
        {"name":"onap/aaf/aaf_service","tags":["2.1.1","2.1.3","2.1.4","2.1.5"]}
    Hence, we need to extract all the tags, and add them to our list of valid or
    invalid tags.
    If we fail to collect the tags, we set the repository_exist flag to false.

    Parameter:
        org_name  : The organization part of the repository. (onap)
        repo_name : The Nexus3 repository name (aaf/aaf_service)
        repo_from_file : The reponame came from an input file.

    Result:
        Will fetch all tags from the Nexus3 repository URL, and store each tag
        in self.valid or self.invalid as a list.
        If no repository is found, self.repository_exist will be set to False.
    """

    def __init__(self, org_name, repo_name, repo_from_file):
        """Initialize this class."""
        TagClass.__init__(self, org_name, repo_name, repo_from_file)
        retries = 0
        # Default to <org>/<repo>
        org_repo_name = "{}/{}".format(org_name, repo_name)
        if repo_from_file:
            org_repo_name = "{}".format(repo_name)
        log.debug("Fetching nexus3 tags for {}".format(org_repo_name))
        while retries < 20:
            try:
                r = _request_get(NEXUS3_BASE + "/v2/" + org_repo_name + "/tags/list")
                break
            except requests.HTTPError as excinfo:
                log.debug("Fetching Nexus3 tags. {}".format(excinfo))
                retries = retries + 1
                if retries > 19:
                    self.repository_exist = False
                    return

        log.debug("r.status_code = {}, ok={}".format(r.status_code, r.status_code == requests.codes.ok))
        if r.status_code == requests.codes.ok:
            raw_tags = r.text
            raw_tags = raw_tags.replace('"', "")
            raw_tags = raw_tags.replace("}", "")
            raw_tags = raw_tags.replace("]", "")
            raw_tags = raw_tags.replace(" ", "")
            raw_tags = raw_tags.split("[")
            TmpSplittedTags = raw_tags[1].split(",")
            if len(TmpSplittedTags) > 0:
                for tag_2_add in TmpSplittedTags:
                    self.add_tag(tag_2_add)
                    log.debug("Nexus {} has tag {}".format(org_repo_name, tag_2_add))
        else:
            self.repository_exist = False


class DockerTagClass(TagClass):
    """Docker tag class.

    This class fetches and stores all docker tags for a repository.

    Doing this manually from command line, you will give this command:
        curl -s https://registry.hub.docker.com/v1/repositories/onap/base_sdc-sanity/tags
    which gives you the following output:
        {"layer": "", "name": "latest"}, {"layer": "", "name": "1.3.0"},
        {"layer": "", "name": "1.3.1"}, {"layer": "", "name": "1.4.0"},
        {"layer": "", "name": "1.4.1"}, {"layer": "", "name": "v1.0.0"}]

    When we fetch the tags from the docker repository url, they are returned like
        [{"layer": "", "name": "latest"}, {"layer": "", "name": "v1.0.0"}]
    Hence, we need to extract all the tags, and add them to our list of valid or
    invalid tags.
    If we fail to collect the tags, we set the repository_exist flag to false.

    Parameter:
        org_name  : The organization part of the repository. (onap)
        repo_name : The Docker Hub repository name (aaf-aaf_service)
        repo_from_file : The reponame came from an input file.

    Result:
        Will fetch all tags from the Docker Repository URL, and store each tag
        in self.valid or self.invalid as a list.
        If no repository is found, self.repository_exist will be set to False.
    """

    _docker_base = "https://registry.hub.docker.com/v1/repositories"

    def __init__(self, org_name, repo_name, repo_from_file):
        """Initialize this class."""
        TagClass.__init__(self, org_name, repo_name, repo_from_file)
        if repo_from_file:
            combined_repo_name = repo_name
        else:
            combined_repo_name = "{}/{}".format(org_name, repo_name)
        log.debug("Fetching docker tags for {}".format(combined_repo_name))
        retries = 0
        while retries < 20:
            try:
                r = _request_get(self._docker_base + "/" + combined_repo_name + "/tags")
                # I got some throttling issues due to to fast between gets, so lets sleep a bit after each
                sleep (0.5)
                break
            except requests.HTTPError as excinfo:
                log.debug("Fetching Docker Hub tags. {}".format(excinfo))
                retries = retries + 1
                if retries > 19:
                    self.repository_exist = False
                    return

        log.debug("r.status_code = {}, ok={}".format(r.status_code, r.status_code == requests.codes.ok))
        pull_rate_limit = False
        if r.status_code == 429:
            # To distinguish between accessing to fast, versus to many to fast.
            pull_rate_limit = ("reached your pull rate limit" in r.text)
        if pull_rate_limit:
            # Throttling in effect. Cancel program
            print_anonymous_throttling_stats()
            store_timestamp_to_last_run_file(lastrun_filename)
            raise requests.HTTPError(
                "Throttling in effect. {} Docker pulls. Wait {} seconds. \n {}".format(
                    len(projects), throttling_delay_seconds, r.text
                )
            )
        elif r.status_code == requests.codes.ok:
            raw_tags = r.text
            raw_tags = raw_tags.replace("}]", "")
            raw_tags = raw_tags.replace("[{", "")
            raw_tags = raw_tags.replace("{", "")
            raw_tags = raw_tags.replace('"', "")
            raw_tags = raw_tags.replace(" ", "")
            TmpSplittedTuple = raw_tags.split("}")
            if len(TmpSplittedTuple) > 0:
                for tuple in TmpSplittedTuple:
                    tmp_tuple = tuple.split(":")
                    if len(tmp_tuple) > 1:
                        self.add_tag(tmp_tuple[2].strip())
                        log.debug("Docker {} has tag {}".format(combined_repo_name, tmp_tuple[2]))
        else:
            self.repository_exist = False


class ProjectClass:
    """Main Project class.

    Main Function of this class, is to , and push the missing images from
    Nexus3 to Docker Hub.

    Parameters:
        nexus_proj :  list with ['org', 'repo', 'dockername']
            ['onap', 'aaf/aaf_service', 'aaf-aaf_service']

    Upon class Initialize the following happens.
      * Set Nexus and Docker repository names.
      * Initialize the Nexus and Docker tag variables.
      * Find which tags are needed to be copied.

    Main external function is docker__tag_push
    """

    def __init__(self, nexus_proj):
        """Initialize this class."""
        self.org_name = nexus_proj[0]
        self.nexus_repo_name = nexus_proj[1]
        repo_from_file = len(nexus_proj[2]) > 0
        if repo_from_file:
            self.docker_repo_name = nexus_proj[2].strip()
        else:
            self._set_docker_repo_name(self.nexus_repo_name)
        self.nexus_tags = NexusTagClass(self.org_name, self.nexus_repo_name, repo_from_file)
        self.docker_tags = DockerTagClass(self.org_name, self.docker_repo_name, repo_from_file)
        self.tags_2_copy = TagClass(self.org_name, self.nexus_repo_name, repo_from_file)
        self._populate_tags_to_copy()
        self.docker_client = docker.from_env()

    def __lt__(self, other):
        """Implement sort order base on Nexus3 repo name."""
        return self.nexus_repo_name < other.nexus_repo_name

    def calc_nexus_project_name(self):
        """Get Nexus3 project name."""
        return self.org_name + "/" + self.nexus_repo_name

    def calc_docker_project_name(self):
        """Get Docker Hub project name."""
        return self.org_name + "/" + self.docker_repo_name

    def _set_docker_repo_name(self, nexus_repo_name):
        """Set Docker Hub repo name.

        Docker repository will be based on the Nexus3 repo name.
        But replacing all '/' with '-'
        """
        self.docker_repo_name = self.nexus_repo_name.replace("/", "-")
        log.debug("ProjName = {} ---> Docker name = {}".format(self.nexus_repo_name, self.docker_repo_name))

    def _populate_tags_to_copy(self):
        """Populate tags_to_copy list.

        Check that all valid Nexus3 tags are among the Docker Hub valid tags.
        If not, add them to the tags_2_copy list.
        """
        log.debug(
            "Populate {} has valid Nexus3 {} and valid Docker Hub {}".format(
                self.docker_repo_name, len(self.nexus_tags.valid), len(self.docker_tags.valid)
            )
        )

        if len(self.nexus_tags.valid) > 0:
            for nexustag in self.nexus_tags.valid:
                if nexustag not in self.docker_tags.valid:
                    log.debug("Need to copy tag {} from {}".format(nexustag, self.nexus_repo_name))
                    self.tags_2_copy.add_tag(nexustag)

    def _pull_tag_push_msg(self, info_text, count, retry_text="", progbar=False):
        """Print a formated message using log.info."""
        due_to_txt = ""
        if len(retry_text) > 0:
            due_to_txt = "due to {}".format(retry_text)
        _attempt_str = "Attempt "
        b4_txt_template = _attempt_str + "{:2d}"
        b4_txt = "".ljust(len(_attempt_str) + 2)
        if count > 1:
            b4_txt = b4_txt_template.format(count)
        if progbar:
            tqdm.tqdm.write("{}: {} {}".format(b4_txt, info_text, due_to_txt))
        else:
            log.info("{}: {} {}".format(b4_txt, info_text, due_to_txt))

    def _docker_pull(self, nexus_image_str, count, tag, retry_text="", progbar=False):
        """Pull an image from Nexus."""
        self._pull_tag_push_msg(
            "Pulling  Nexus3 image {} with tag {}".format(self.calc_nexus_project_name(), tag), count, retry_text
        )
        image = self.docker_client.images.pull(nexus_image_str)
        return image

    def _docker_tag(self, count, image, tag, retry_text="", progbar=False):
        """Tag the image with proper docker name and version."""
        self._pull_tag_push_msg(
            "Creating docker image {} with tag {}".format(self.calc_docker_project_name(), tag), count, retry_text
        )
        image.tag(self.calc_docker_project_name(), tag=tag)

    def _docker_push(self, count, image, tag, retry_text, progbar=False):
        """Push the docker image to Docker Hub."""
        self._pull_tag_push_msg(
            "Pushing  docker image {} with tag {}".format(self.calc_docker_project_name(), tag), count, retry_text
        )
        res = self.docker_client.images.push(self.calc_docker_project_name(), tag=tag)
        return res

    def _docker_cleanup(self, count, image, tag, retry_text="", progbar=False):
        """Remove the local copy of the image."""
        image_id = _format_image_id(image.short_id)
        self._pull_tag_push_msg(
            "Cleanup  docker image {} with tag {} and id {}".format(self.calc_docker_project_name(), tag, image_id),
            count,
            retry_text,
        )
        self.docker_client.images.remove(image.id, force=True)

    def docker_pull_tag_push(self, progbar=False):
        """Copy all missing Docker Hub images from Nexus3.

        This is the main function which will copy a specific tag from Nexu3
        to Docker Hub repository.

        It has 4 stages, pull, tag, push and cleanup.
        Each of these stages, will be retried a number of times upon failures.
        """
        if len(self.tags_2_copy.valid) == 0:
            return

        for tag in self.tags_2_copy.valid:
            org_path = _remove_http_from_url(NEXUS3_BASE)
            nexus_image_str = "{}/{}/{}:{}".format(org_path, self.org_name, self.nexus_repo_name, tag)
            log.debug("Nexus Image Str = {}".format(nexus_image_str))
            for stage in ["pull", "tag", "push", "cleanup"]:
                cnt_break_loop = 1
                retry_text = ""
                while True:
                    try:
                        log.debug("stage = {}. cnt_break_loop {}, reason {}".format(stage, cnt_break_loop, retry_text))
                        if stage == "pull":
                            image = self._docker_pull(nexus_image_str, cnt_break_loop, tag, retry_text, progbar)
                            break

                        if stage == "tag":
                            self._docker_tag(cnt_break_loop, image, tag, retry_text, progbar)
                            break

                        if stage == "push":
                            res = self._docker_push(cnt_break_loop, image, tag, retry_text, progbar)
                            if not res:
                                log.debug("Just checking res variable to get rid of warning")
                            # TODO: Should check for res containing Error or Throttling. Not sure how
                            # use getattr? search for "pull rate limit"
                            #       Return type: (generator or str)
                            break

                        if stage == "cleanup":
                            self._docker_cleanup(cnt_break_loop, image, tag, retry_text, progbar)
                            break
                    except socket.timeout:
                        retry_text = "Socket Timeout"
                    except requests.exceptions.ConnectionError:
                        retry_text = "Connection Error"
                    except urllib3.exceptions.ReadTimeoutError:
                        retry_text = "Read Timeout Error"
                    except docker.errors.APIError:
                        retry_text = "API Error"
                    cnt_break_loop = cnt_break_loop + 1
                    if cnt_break_loop > 90:
                        raise requests.HTTPError(retry_text)


def repo_is_in_file(check_repo="", repo_file_name=""):
    """Function to verify of a repo name exists in a file name.

    The file contains rows of repo names to be included.
        acumos-portal-fe
        acumos/acumos-axure-client

    Function will return True if a match is found

    """
    with open("{}".format(repo_file_name)) as f:
        for line in f.readlines():
            row = line.rstrip()
            reponame = row.split(";")[0]
            log.debug("Comparing {} with {} from file".format(check_repo, reponame))
            if check_repo == reponame:
                log.debug("Found a match")
                return True
    log.debug("NO match found")
    return False


def get_docker_name_from_file(check_repo="", repo_file_name=""):
    """Function to verify of a repo name exists in a file name.

    The file contains rows of repo names to be included.
        acumos-portal-fe
        acumos/acumos-axure-client

    Function will return True if a match is found

    """
    with open("{}".format(repo_file_name)) as f:
        for line in f.readlines():
            row = line.rstrip()
            reponame = row.split(";")[0]
            dockername = row.split(";")[1]
            log.debug("Comparing {} with {} from file".format(check_repo, reponame))
            if check_repo == reponame:
                log.debug("Found a match")
                return dockername
    log.debug("NO match found")
    return ""


def get_nexus3_catalog(org_name="", find_pattern="", exact_match=False, repo_is_filename=False):
    """Main function to collect all Nexus3 repositories.

    This function will collect the Nexus catalog for all projects starting with
    'org_name' as well as containing a pattern if specified.
    If exact_match is specified, it will use the pattern as a unique repo name within the org_name.

    If you do it manually, you give the following command.
        curl -s https://nexus3.onap.org:10002/v2/_catalog

    which gives you the following output.
        {"repositories":["dcae_dmaapbc","onap/aaf/aaf-base-openssl_1.1.0",
        "onap/aaf/aaf-base-xenial","onap/aaf/aaf_agent","onap/aaf/aaf_cass",
        "onap/aaf/aaf_cm","onap/aaf/aaf_config","onap/aaf/aaf_core"]}

    Nexus3 catalog starts with <org_name>/<repo name>

    Parameters:
        org_name        : Organizational name, for instance 'onap'
        find_pattern    : A pattern, that if specified, needs to be part of the
                          repository name.
                          for instance,
                           ''     : this pattern finds all repositories.
                           'eleo' : this pattern finds all repositories with 'eleo'
                                    in its name. --> chameleon
        exact_match     : If specified, find_pattern is a unique repo name
        repo_is_filename: If specified, find_pattern is a filename, which contains a repo name per row
                            org_name is irrelevant in this case

    """
    global NexusCatalog
    global project_max_len_chars

    project_max_len_chars = 0
    containing_str = ""
    if len(find_pattern) > 0:
        containing_str = ', and containing "{}"'.format(find_pattern)
    if exact_match:
        containing_str = ', and reponame = "{}"'.format(find_pattern)
    if repo_is_filename:
        containing_str = ', and repos are found in "{}"'.format(find_pattern)
    info_str = "Collecting information from Nexus from projects with org = {}".format(org_name)
    log.info("{}{}.".format(info_str, containing_str))

    try:
        r = _request_get(NEXUS3_CATALOG)
    except requests.HTTPError as excinfo:
        log.info("Fetching Nexus3 catalog. {}".format(excinfo))
        return False

    log.debug("r.status_code = {}, ok={}".format(r.status_code, r.status_code == requests.codes.ok))
    if r.status_code == requests.codes.ok:
        raw_catalog = r.text
        raw_catalog = raw_catalog.replace('"', "")
        raw_catalog = raw_catalog.replace(" ", "")
        raw_catalog = raw_catalog.replace("}", "")
        raw_catalog = raw_catalog.replace("[", "")
        raw_catalog = raw_catalog.replace("]", "")
        raw_catalog = raw_catalog.split(":")
        TmpCatalog = raw_catalog[1].split(",")
        for word in TmpCatalog:
            # Remove all projects that do not start with org_name
            use_this_repo = False
            if repo_is_filename and repo_is_in_file(word, find_pattern):
                use_this_repo = True
                project = [org_name, word, get_docker_name_from_file(word, find_pattern)]
            else:
                if word.startswith(org_name):
                    # Remove org_name/ from word, so we only get repository left
                    project = [org_name, word[len(org_name) + 1 :], ""]
                    # If a specific search string has been specified, search for it
                    # Empty string will match all words
                    if word.find(find_pattern) >= 0 and not exact_match:
                        use_this_repo = True
                    if exact_match and project[1] == find_pattern:
                        use_this_repo = True
            if use_this_repo:
                NexusCatalog.append(project)
                log.debug("Added project {} to my list".format(project[1]))
                if len(project[1]) > project_max_len_chars:
                    project_max_len_chars = len(project[1])
        log.debug(
            "# TmpCatalog {}, NexusCatalog {}, DIFF = {}".format(
                len(TmpCatalog), len(NexusCatalog), len(TmpCatalog) - len(NexusCatalog)
            )
        )
    return True


def fetch_all_tags(progbar=False):
    """Fetch all tags function.

    This function will use multi-threading to fetch all tags for all projects in
    Nexus3 Catalog.
    """
    NbrProjects = len(NexusCatalog)
    log.info(
        "Fetching tags from Nexus3 and Docker Hub for {} projects with version regexp >>{}<<".format(
            NbrProjects, VERSION_REGEXP
        )
    )
    if progbar:
        pbar = tqdm.tqdm(total=NbrProjects, bar_format="{l_bar}{bar}|{n_fmt}/{total_fmt} [{elapsed}]")

    def _fetch_all_tags(proj):
        """Helper function for multi-threading.

        This function, will create an instance of ProjectClass (which triggers
        the project class fetching all Nexus3/Docker Hub tags)
        Then adding this instance to the project list.

            Parameters:
                proj : Tuple with 'org' and 'repo'
                    ('onap', 'aaf/aaf_service')
        """
        new_proj = ProjectClass(proj)
        projects.append(new_proj)
        if progbar:
            pbar.update(1)

    pool = ThreadPool(multiprocessing.cpu_count())
    pool.map(_fetch_all_tags, NexusCatalog)
    pool.close()
    pool.join()

    if progbar:
        pbar.close()
    projects.sort()


def copy_from_nexus_to_docker(progbar=False):
    """Copy all missing tags.

    This function will use multi-threading to copy all missing tags in the project list.
    """
    _tot_tags = 0
    for proj in projects:
        _tot_tags = _tot_tags + len(proj.tags_2_copy.valid)
    log.info("About to start copying from Nexus3 to Docker Hub for {} missing tags".format(_tot_tags))
    if progbar:
        pbar = tqdm.tqdm(total=_tot_tags, bar_format="{l_bar}{bar}|{n_fmt}/{total_fmt} [{elapsed}]")

    def _docker__tag_push(proj):
        """Helper function for multi-threading.

        This function, will call the ProjectClass proj's docker_pull_tag_push.

            Parameters:
                proj : Tuple with 'org' and 'repo'
                    ('onap', 'aaf/aaf_service')
        """
        proj.docker_pull_tag_push(progbar)
        if progbar:
            pbar.update(len(proj.tags_2_copy.valid))

    pool = ThreadPool(multiprocessing.cpu_count())
    pool.map(_docker__tag_push, projects)
    pool.close()
    pool.join()
    if progbar:
        pbar.close()


def fetch_last_nexus_repo_from_last_time(file_name):
    # Fetching nexus3 repo name from file
    # This is the last repo from the previous batch processed

    last_nexus_repo = ""
    try:
        with open(file_name, "r") as fp:
            last_nexus_repo = fp.read().strip()
    except OSError:
        last_nexus_repo = ""
    return last_nexus_repo


def store_last_nexus_repo_from_this_time(file_name):
    # Store the last run timestamp to permanent storage
    last_nexus_repo = "{}/{}".format(NexusCatalog[-1][0], NexusCatalog[-1][1])
    try:
        with open(file_name, "w") as _file:
            _file.write("{}".format(last_nexus_repo))
    except OSError:
        log.error("Could not write last nexus repo to file")


def use_next_batch_from_nexus3(file_name):
    tmp_catalog = []
    global NexusCatalog, OrigNexusCatalog
    current_nbr_nexus3_repos = len(NexusCatalog)
    if nexus3_batch_size > current_nbr_nexus3_repos:
        # Nothing to do, we have less repos than throttling limit
        log.debug("Using all repos we have gathered.")
        return
    log.info("Will only use {} of the collected {} repos.".format(nexus3_batch_size, len(NexusCatalog)))
    last_repo_name = fetch_last_nexus_repo_from_last_time(file_name)
    log.info("Starting from repo {}".format(last_repo_name))
    for item in NexusCatalog:
        # Check if we have max number of repos in tmp_catalog
        if len(tmp_catalog) >= nexus3_batch_size:
            break
        repo_name = "{}/{}".format(item[0], item[1])
        # Check if we have reached the last repo done on previous run
        if last_repo_name < repo_name:
            tmp_catalog.append(item)

    # Check if tmp_catalog is maxed
    if len(tmp_catalog) < nexus3_batch_size:
        # It was not maxed, add from beginning of NexusCatalog
        for item in NexusCatalog:
            if len(tmp_catalog) >= nexus3_batch_size:
                break
            repo_name = "{}/{}".format(item[0], item[1])
            tmp_catalog.append(item)
    OrigNexusCatalog = NexusCatalog.copy()
    NexusCatalog = tmp_catalog.copy()


def fetch_my_public_ip():
    # fetches the public IP for this server
    ip = requests.get("https://api.ipify.org").text
    log.debug("My public IP address is: {}".format(ip))
    return ip.strip()


def copy_permanent_data_files_from_s3_bucket_to_local(local_target_dir):
    # Retrieves the permanent data files from s3 bucket, and stores
    # them to temporary directory
    # This function is unit tested only with s3 credentials on local computer
    if not USE_S3_BUCKET:
        return
    s3 = boto3.resource("s3")
    s3_bucket = s3.Bucket(s3_bucket_name)
    for obj in s3_bucket.objects.all():
        s3_bucket.download_file(obj.key, "{}/{}".format(local_target_dir, obj.key))


def store_permanent_data_files_from_local_to_s3_bucket(local_source_dir):
    # Store all files from the temporary directory to permanent storage
    # in an s3 bucket
    # This function is unit tested only with s3 credentials on local computer
    if not USE_S3_BUCKET:
        return
    s3 = boto3.resource("s3")
    s3_bucket = s3.Bucket(s3_bucket_name)
    for filename in os.listdir(local_source_dir):
        f = os.path.join(local_source_dir, filename)
        s3_bucket.upload_file(f, filename)


def delete_file_from_s3_bucket(delete_this_file):
    # Delete one (1) file from the permanent storage
    # in an s3 bucket
    # This function is unit tested only with s3 credentials on local computer
    if not USE_S3_BUCKET:
        return
    s3 = boto3.resource("s3")
    s3_object = s3.Object(s3_bucket_name, delete_this_file)
    s3_object.delete()


def fetch_last_run_timestamp(file_name):
    # Fetching file with a list of IP; TimeStamp
    # Returning the TimeStamp that corrsponds to my public_ip

    date_time_str = no_timestamp_str
    my_ip = fetch_my_public_ip()

    try:
        with open(file_name, "r") as fp:
            for i in fp.readlines():
                tmp = i.split(";")
                log.debug("tmp[0]={}, tmp[1]={}".format(tmp[0], tmp[1]))
                if tmp[0].strip() == my_ip:
                    log.debug("Found correct IP")
                    date_time_str = tmp[1].strip()
                    break
        log.debug("Did not find my IP ({}) among the list of last run timestamps".format(my_ip))

    except OSError:
        date_time_str = no_timestamp_str
    try:
        date_time_obj = datetime.datetime.strptime(date_time_str, lastrun_format)
    except ValueError:
        log.error("Wrong date format found >>{}<<, expected >>{}<<".format(date_time_str, lastrun_format))
        log.error("For now, using default old timestamp {}".format(no_timestamp_str))
        date_time_obj = datetime.datetime.strptime(no_timestamp_str, lastrun_format)
    return date_time_obj


def store_timestamp_to_last_run_file(file_name):
    # Store the last run timestamp
    sttime = datetime.datetime.now().strftime(lastrun_format)
    my_ip = fetch_my_public_ip()
    ip_time_lst = []
    found_my_ip = False
    try:
        with open(file_name, "r") as fp:
            for i in fp.readlines():
                tmp = i.split(";")
                tmp[0] = tmp[0].strip()
                tmp[1] = tmp[1].strip()
                if tmp[0] == my_ip:
                    tmp[1] = sttime
                    log.debug("Replacing timestamp for IP {} in last_run file".format(my_ip))
                    found_my_ip = True
                ip_time_lst.append((tmp[0], tmp[1]))
    except OSError:
        log.error("Last run timestamp file not found, assuming first time")
    if not found_my_ip:
        log.debug("Adding this IP {} and timestamp {} to the file last_run".format(my_ip, sttime))
        ip_time_lst.append((my_ip, sttime))
    try:
        with open(file_name, "w") as _file:
            for row in ip_time_lst:
                _file.write("{} ; {}\n".format(row[0], row[1]))
    except OSError:
        log.error("Could not write timestamps to file")


def to_close_to_last_run(last_run, throttling_delay_seconds):
    # Checks if interval between now and last_run is more than throttling delay.
    earliest_time_for_next_run = last_run + datetime.timedelta(seconds=throttling_delay_seconds)
    return earliest_time_for_next_run >= datetime.datetime.now()


def print_nexus_docker_proj_names():
    """Print Nexus3 - Docker Hub repositories."""
    fmt_str = "{:<" + str(project_max_len_chars) + "} : "
    log.info("")
    log_str = fmt_str.format(NEXUS3_PROJ_NAME_HEADER)
    log_str = "{}{}".format(log_str, DOCKER_PROJ_NAME_HEADER)
    log.info(log_str)
    log.info("-" * project_max_len_chars * 2)
    docker_i = 0
    for proj in projects:
        log_str = fmt_str.format(proj.nexus_repo_name)
        log_str = "{}{}".format(log_str, proj.docker_repo_name)
        log.info(log_str)
        docker_i = docker_i + 1
    log.info("")


def print_tags_header(header_str, col_1_str):
    """Print simple header."""
    fmt_str = "{:<" + str(project_max_len_chars) + "} : "
    log.info(header_str)
    log_str = fmt_str.format(col_1_str)
    log_str = "{}{}".format(log_str, "Tags")
    log.info(log_str)
    log.info("-" * project_max_len_chars * 2)


def print_tags_data(proj_name, tags):
    """Print tag data."""
    fmt_str = "{:<" + str(project_max_len_chars) + "} : "
    if len(tags) > 0:
        log_str = fmt_str.format(proj_name)
        tag_i = 0
        for tag in tags:
            if tag_i > 0:
                log_str = "{}, ".format(log_str)
            log_str = "{}{}".format(log_str, tag)
            tag_i = tag_i + 1
        log.info(log_str)


def print_nexus_valid_tags():
    """Print Nexus valid tags."""
    print_tags_header("Nexus Valid Tags", NEXUS3_PROJ_NAME_HEADER)
    for proj in projects:
        print_tags_data(proj.nexus_repo_name, proj.nexus_tags.valid)
    log.info("")


def print_nexus_invalid_tags():
    """Print Nexus invalid tags."""
    print_tags_header("Nexus InValid Tags", NEXUS3_PROJ_NAME_HEADER)
    for proj in projects:
        print_tags_data(proj.nexus_repo_name, proj.nexus_tags.invalid)
    log.info("")


def print_docker_valid_tags():
    """Print Docker valid tags."""
    print_tags_header("Docker Valid Tags", DOCKER_PROJ_NAME_HEADER)
    for proj in projects:
        print_tags_data(proj.docker_repo_name, proj.docker_tags.valid)
    log.info("")


def print_docker_invalid_tags():
    """Print Docker invalid tags."""
    print_tags_header("Docker InValid Tags", DOCKER_PROJ_NAME_HEADER)
    for proj in projects:
        print_tags_data(proj.docker_repo_name, proj.docker_tags.invalid)
    log.info("")


def print_stats():
    """Print simple repo/tag statistics."""
    print_tags_header("Tag statistics (V=Valid, I=InValid)", NEXUS3_PROJ_NAME_HEADER)
    fmt_str = "{:<" + str(project_max_len_chars) + "} : "
    for proj in projects:
        log.info(
            "{}Nexus V:{} I:{} -- Docker V:{} I:{}".format(
                fmt_str.format(proj.nexus_repo_name),
                len(proj.nexus_tags.valid),
                len(proj.nexus_tags.invalid),
                len(proj.docker_tags.valid),
                len(proj.docker_tags.invalid),
            )
        )
    log.info("")


def print_missing_docker_proj():
    """Print missing docker repos."""
    log.info("Missing corresponding Docker Project")
    fmt_str = "{:<" + str(project_max_len_chars) + "} : "
    log_str = fmt_str.format(NEXUS3_PROJ_NAME_HEADER)
    log_str = "{}{}".format(log_str, DOCKER_PROJ_NAME_HEADER)
    log.info(log_str)
    log.info("-" * project_max_len_chars * 2)
    all_docker_repos_found = True
    for proj in projects:
        if not proj.docker_tags.repository_exist:
            log_str = fmt_str.format(proj.nexus_repo_name)
            log_str = "{}{}".format(log_str, proj.docker_repo_name)
            log.info(log_str)
            all_docker_repos_found = False
    if all_docker_repos_found:
        log.info("All Docker Hub repos found.")
    log.info("")


def print_nexus_tags_to_copy():
    """Print tags that needs to be copied."""
    log.info("Nexus project tags to copy to docker")
    fmt_str = "{:<" + str(project_max_len_chars) + "} : "
    log_str = fmt_str.format(NEXUS3_PROJ_NAME_HEADER)
    log_str = "{}{}".format(log_str, "Tags to copy")
    log.info(log_str)
    log.info("-" * project_max_len_chars * 2)
    for proj in projects:
        if len(proj.tags_2_copy.valid) > 0:
            log_str = ""
            tag_i = 0
            log_str = fmt_str.format(proj.nexus_repo_name)
            for tag in proj.tags_2_copy.valid:
                if tag_i > 0:
                    log_str = "{}, ".format(log_str)
                log_str = "{}{}".format(log_str, tag)
                tag_i = tag_i + 1
            log.info(log_str)
    log.info("")


def print_nbr_tags_to_copy():
    """Print how many tags that needs to be copied."""
    _tot_tags = 0
    for proj in projects:
        _tot_tags = _tot_tags + len(proj.tags_2_copy.valid)
    log.info("Summary: {} tags that should be copied from Nexus3 to Docker Hub.".format(_tot_tags))


def print_anonymous_throttling_stats():
    """Print anonymous throttling stats for this session."""
    current = AnonymousThrottlingStatus()
    log.info("Anonymous dockerhub throttling limit={}, remaining now {}.".format(current.limit, current.remaining))


def filter_active(pattern=""):
    ## TODO Change to != ""
    return pattern != ""


def start_point(
    org_name,
    find_pattern="",
    exact_match=False,
    summary=False,
    verbose=False,
    copy=False,
    progbar=False,
    repofile=False,
    version_regexp="",
    ignore_throttle_delay=False,
    in_s3_bucket_name="",
):
    """Main function."""
    global s3_bucket_name
    s3_bucket_name = in_s3_bucket_name
    if len(s3_bucket_name) == 0:
        s3_bucket_name = def_s3_bucket_name

    log.info("Using S3 bucket : {}".format(USE_S3_BUCKET))
    log.info("S3 bucket name for permanent data : {}".format(s3_bucket_name))

    copy_permanent_data_files_from_s3_bucket_to_local(local_s3_copy)
    # Check if last run was to close, avoid docker throttling issues
    last_run_timestamp = fetch_last_run_timestamp(lastrun_filename)
    if not ignore_throttle_delay:
        if to_close_to_last_run(last_run_timestamp, throttling_delay_seconds):
            print_anonymous_throttling_stats()
            log.error(
                "You need to wait {} seconds since last run which was done at {}".format(
                    throttling_delay_seconds,
                    last_run_timestamp,
                )
            )
            return

    # Verify find_pattern and specified_repo are not both used.
    if len(find_pattern) == 0 and exact_match:
        log.error("You need to provide a Pattern to go with the --exact flag")
        return
    initialize(org_name, version_regexp)
    if not validate_regexp():
        log.error("Found issues with the provided regexp >>{}<< ".format(VERSION_REGEXP))
        return
    if not get_nexus3_catalog(org_name, find_pattern, exact_match, repofile):
        log.info("Could not get any catalog from Nexus3 with org = {}".format(org_name))
        return

    if not filter_active(find_pattern):
        use_next_batch_from_nexus3(lastnexusrepo_filename)

    fetch_all_tags(progbar)
    if verbose:
        print_nexus_docker_proj_names()
        print_nexus_valid_tags()
        print_nexus_invalid_tags()
        print_docker_valid_tags()
        print_docker_invalid_tags()
        print_stats()
    if summary or verbose:
        print_missing_docker_proj()
        print_nexus_tags_to_copy()
        print_anonymous_throttling_stats()
    if copy:
        copy_from_nexus_to_docker(progbar)
        if not filter_active(find_pattern):
            store_last_nexus_repo_from_this_time(lastnexusrepo_filename)
    else:
        print_nbr_tags_to_copy()

    store_timestamp_to_last_run_file(lastrun_filename)
    store_permanent_data_files_from_local_to_s3_bucket(local_s3_copy)
    # Remove temporary folder, since all files are now on s3 bucket
    if os.path.exists(local_s3_copy) and os.path.isdir(local_s3_copy):
        shutil.rmtree(local_s3_copy)
