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

import logging
import re
import socket

import docker
import requests
import tqdm
import urllib3

log = logging.getLogger(__name__)

NexusCatalog = []
projects = []
TotTagsToBeCopied = 0

NEXUS3_BASE = ""
NEXUS3_CATALOG = ""
NEXUS3_PROJ_NAME_HEADER = ""
DOCKER_PROJ_NAME_HEADER = ""


def _remove_http_from_url(url):
    """Remove http[s]:// from url."""
    if url.startswith('https://'):
        return url[len('https://'):]
    if url.startswith('http://'):
        return url[len('http://'):]
    return url


def _format_image_id(id):
    """Remove sha256: from beginning of string."""
    if id.startswith("sha256:"):
        return id[len('sha256:'):]
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


def initialize(org_name):
    """Set constant strings."""
    global NEXUS3_BASE
    global NEXUS3_CATALOG
    global NEXUS3_PROJ_NAME_HEADER
    global DOCKER_PROJ_NAME_HEADER
    NEXUS3_BASE = "https://nexus3.{}.org:10002".format(org_name)
    NEXUS3_CATALOG = NEXUS3_BASE + "/v2/_catalog"
    NEXUS3_PROJ_NAME_HEADER = "Nexus3 Project Name"
    DOCKER_PROJ_NAME_HEADER = "Docker HUB Project Name"


class TagClass:
    """Base class for Nexus3 and Docker Hub tag class.

    This class contains the actual valid and invalid tags for a repository,
    as well as an indication if the repository exist or not.

    A valid tag has the following format #.#.# (1.2.3, or 1.22.333)

    Parameter:
        org_name  : The organization part of the repository. (onap)
        repo_name : The Nexus3 repository name (aaf/aaf_service)
    """

    def __init__(self, org_name, repo_name):
        """Initialize this class."""
        self.valid = []
        self.invalid = []
        self.repository_exist = True
        self.org = org_name
        self.repo = repo_name

    def _validate_tag(self, check_tag):
        """Local helper function to simplify validity check of version number.

        Returns true or false, depending if the version pattern is a valid one.
        Valid pattern is #.#.#, or in computer term "^\d+.\d+.\d+$"

        Future pattern : x.y.z-KEYWORD-yyyymmddThhmmssZ
          where keyword = STAGING or SNAPSHOT
          '^\d+.\d+.\d+-(STAGING|SNAPSHOT)-(20\d{2})(\d{2})(\d{2})T([01]\d|2[0-3])([0-5]\d)([0-5]\d)Z$'
        """
        pattern = re.compile(r'^\d+.\d+.\d+$')
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


class NexusTagClass (TagClass):
    """Nexus Tag class.

    This class fetches and stores all Nexus3 tags for a repository.

    Doing this manually from command line, you will give this command:
        curl -s https://nexus3.onap.org:10002/v2/onap/aaf/aaf_service/tags/list
    which gives you the following output:
        {"name":"onap/aaf/aaf_service","tags":["2.1.1","2.1.3","2.1.4","2.1.5","2.1.6","2.1.7","2.1.8"]}

    When we fetch the tags from the Nexus3 repository url, they are returned like
        {"name":"onap/aaf/aaf_service","tags":["2.1.1","2.1.3","2.1.4","2.1.5"]}
    Hence, we need to extract all the tags, and add them to our list of valid or
    invalid tags.
    If we fail to collect the tags, we set the repository_exist flag to false.

    Parameter:
        org_name  : The organization part of the repository. (onap)
        repo_name : The Nexus3 repository name (aaf/aaf_service)

    Result:
        Will fetch all tags from the Nexus3 repository URL, and store each tag
        in self.valid or self.invalid as a list.
        If no repository is found, self.repository_exist will be set to False.
    """

    def __init__(self, org_name, repo_name):
        """Initialize this class."""
        TagClass.__init__(self, org_name, repo_name)
        log.debug("Fetching nexus3 tags for {}/{}".format(org_name, repo_name))
        try:
            r = _request_get(NEXUS3_BASE + "/v2/" + org_name + "/" + repo_name + "/tags/list")
        except requests.HTTPError as excinfo:
            log.debug("Fetching Nexus3 tags. {}".format(excinfo))
            self.repository_exist = False
            return

        log.debug("r.status_code = {}, ok={}".format(
            r.status_code, r.status_code == requests.codes.ok))
        if r.status_code == requests.codes.ok:
            raw_tags = r.text
            raw_tags = raw_tags.replace('"', '')
            raw_tags = raw_tags.replace('}', '')
            raw_tags = raw_tags.replace(']', '')
            raw_tags = raw_tags.replace(' ', '')
            raw_tags = raw_tags.split('[')
            TmpSplittedTags = raw_tags[1].split(',')
            if len(TmpSplittedTags) > 0:
                for tag_2_add in TmpSplittedTags:
                    self.add_tag(tag_2_add)
                    log.debug("Nexus {}/{} has tag {}".format(
                        org_name, repo_name, tag_2_add))
        else:
            self.repository_exist = False


class DockerTagClass (TagClass):
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

    Result:
        Will fetch all tags from the Docker Repository URL, and store each tag
        in self.valid or self.invalid as a list.
        If no repository is found, self.repository_exist will be set to False.
    """

    _docker_base = "https://registry.hub.docker.com/v1/repositories"

    def __init__(self, org_name, repo_name):
        """Initialize this class."""
        TagClass.__init__(self, org_name, repo_name)
        log.debug("Fetching docker tags for {}/{}".format(org_name, repo_name))
        try:
            r = _request_get(self._docker_base + "/" + org_name + "/" + repo_name + "/tags")
        except requests.HTTPError as excinfo:
            log.debug("Fetching Docker Hub tags. {}".format(excinfo))
            self.repository_exist = False
            return
        log.debug("r.status_code = {}, ok={}".format(
            r.status_code, r.status_code == requests.codes.ok))
        if r.status_code == requests.codes.ok:
            raw_tags = r.text
            raw_tags = raw_tags.replace('}]', '')
            raw_tags = raw_tags.replace('[{', '')
            raw_tags = raw_tags.replace('{', '')
            raw_tags = raw_tags.replace('"', '')
            raw_tags = raw_tags.replace(' ', '')
            TmpSplittedTuple = raw_tags.split('}')
            if len(TmpSplittedTuple) > 0:
                for tuple in TmpSplittedTuple:
                    tmp_tuple = tuple.split(':')
                    if len(tmp_tuple) > 1:
                        self.add_tag(tmp_tuple[2].strip())
                        log.debug("Docker {}/{} has tag {}".format(
                            org_name, repo_name, tmp_tuple[2]))
        else:
            self.repository_exist = False


class ProjectClass:
    """Main Project class.

    Main Function of this class, is to pull, and push the missing images from
    Nexus3 to Docker Hub.

    Parameters:
        nexus_proj : Tuple with 'org' and 'repo'
            ('onap', 'aaf/aaf_service')

    Upon class Initialize the following happens.
      * Set Nexus and Docker repository names.
      * Initialize the Nexus and Docker tag variables.
      * Find which tags are needed to be copied.

    Main external function is docker_pull_tag_push
    """

    def __init__(self, nexus_proj):
        """Initialize this class."""
        self.org_name = nexus_proj[0]
        self.nexus_repo_name = nexus_proj[1]
        self._set_docker_repo_name(self.nexus_repo_name)
        self.nexus_tags = NexusTagClass(self.org_name, self.nexus_repo_name)
        self.docker_tags = DockerTagClass(self.org_name, self.docker_repo_name)
        self.tags_2_copy = TagClass(self.org_name, self.nexus_repo_name)
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
        self.docker_repo_name = self.nexus_repo_name.replace('/', '-')
        log.debug("ProjName = {} ---> Docker name = {}".format(
            self.nexus_repo_name, self.docker_repo_name))

    def _populate_tags_to_copy(self):
        """Populate tags_to_copy list.

        Check that all valid Nexus3 tags are among the Docker Hub valid tags.
        If not, add them to the tags_2_copy list.
        """
        log.debug('Populate {} has valid Nexus3 {} and valid Docker Hub {}'.format(
            self.docker_repo_name,
            len(self.nexus_tags.valid), len(self.docker_tags.valid)))

        if len(self.nexus_tags.valid) > 0:
            for nexustag in self.nexus_tags.valid:
                if not nexustag in self.docker_tags.valid:
                    log.debug('Need to copy tag {} from {}'.format(nexustag, self.nexus_repo_name))
                    self.tags_2_copy.add_tag(nexustag)

    def _pull_tag_push_msg(self, info_text, count, retry_text='', progbar=False):
        """Print a formated message using log.info."""
        due_to_txt = ''
        if len(retry_text) > 0:
            due_to_txt = 'due to {}'.format(retry_text)

        b4_txt_template = 'Attempt {}'
        b4_txt = ''.ljust(len(b4_txt_template)-1)
        if count > 1:
            b4_txt = b4_txt_template.format(count)
        if progbar:
            tqdm.tqdm.write("{}: {} {}".format(b4_txt, info_text, due_to_txt))
        else:
            log.info("{}: {} {}".format(b4_txt, info_text, due_to_txt))

    def _docker_pull(self, nexus_image_str, count, tag, retry_text='', progbar=False):
        """Pull an image from Nexus."""
        self._pull_tag_push_msg('Pulling  Nexus3 image {} with tag {}'.format(
            self.calc_nexus_project_name(), tag), count, retry_text)
        image = self.docker_client.images.pull(nexus_image_str)
        return image

    def _docker_tag(self, count, image, tag, retry_text='', progbar=False):
        """Tag the image with proper docker name and version."""
        self._pull_tag_push_msg('Creating docker image {} with tag {}'.format(
            self.calc_docker_project_name(), tag), count, retry_text)
        image.tag(self.calc_docker_project_name(), tag=tag)

    def _docker_push(self, count, image, tag, retry_text, progbar=False):
        """Push the docker image to Docker Hub."""
        self._pull_tag_push_msg('Pushing  docker image {} with tag {}'.format(
            self.calc_docker_project_name(), tag), count, retry_text)
        self.docker_client.images.push(self.calc_docker_project_name(), tag=tag)

    def _docker_cleanup(self, count, image, tag, retry_text='', progbar=False):
        """Remove the local copy of the image."""
        image_id = _format_image_id(image.short_id)
        self._pull_tag_push_msg('Cleanup  docker image {} with tag {} and id {}'.format(
            self.calc_docker_project_name(), tag, image_id), count, retry_text)
        self.docker_client.images.remove(image.id, force=True)

    def docker_pull_tag_push(self, progbar=False):
        """Copy all missing Docker Hub images from Nexus3.

        This is the main function which will copy a specific tag from Nexu3
        to Docker Hub repository.

        It has 4 stages, pull, tag, push and cleanup.
        Each of these stages, will be retried 10 times upon failures.
        """
        if len(self.tags_2_copy.valid) == 0:
            return

        for tag in self.tags_2_copy.valid:
            org_path = _remove_http_from_url(NEXUS3_BASE)
            nexus_image_str = '{}/{}/{}:{}'.format(org_path, self.org_name, self.nexus_repo_name, tag)
            log.debug("Nexus Image Str = {}".format(nexus_image_str))
            for stage in ['pull', 'tag', 'push', 'cleanup']:
                cnt_break_loop = 1
                retry_text = ''
                while (True):
                    try:
                        log.debug('stage = {}. cnt_break_loop {}, reason {}'.format(stage, cnt_break_loop, retry_text))
                        if stage == 'pull':
                            image = self._docker_pull(nexus_image_str, cnt_break_loop, tag, retry_text, progbar)
                            break

                        if stage == 'tag':
                            self._docker_tag(cnt_break_loop, image, tag, retry_text, progbar)
                            break

                        if stage == 'push':
                            self._docker_push(cnt_break_loop, image, tag, retry_text, progbar)
                            break

                        if stage == 'cleanup':
                            self._docker_cleanup(cnt_break_loop, image, tag, retry_text, progbar)
                            break
                    except socket.timeout:
                        retry_text = 'Socket Timeout'
                    except requests.exceptions.ConnectionError:
                        retry_text = 'Connection Error'
                    except urllib3.exceptions.ReadTimeoutError:
                        retry_text = 'Read Timeout Error'
                    except docker.errors.APIError:
                        retry_text = 'API Error'
                    cnt_break_loop = cnt_break_loop + 1
                    if (cnt_break_loop > 40):
                        raise requests.HTTPError(retry_text)


def get_nexus3_catalog(org_name='', find_pattern=''):
    """Main function to collect all Nexus3 repositories.

    This function will collect the Nexus catalog for all projects starting with
    'org_name' as well as containing a pattern if specified.

    If you do it manually, you give the following command.
        curl -s https://nexus3.onap.org:10002/v2/_catalog

    which gives you the following output.
        {"repositories":["dcae_dmaapbc","onap/aaf/aaf-base-openssl_1.1.0",
        "onap/aaf/aaf-base-xenial","onap/aaf/aaf_agent","onap/aaf/aaf_cass",
        "onap/aaf/aaf_cm","onap/aaf/aaf_config","onap/aaf/aaf_core"]}

    Nexus3 catalog starts with <org_name>/<repo name>

    Parameters:
        org_name     : Organizational name, for instance 'onap'
        find_pattern : A pattern, that if specified, needs to be part of the
                       repository name.
                        for instance,
                         ''     : this pattern finds all repositories.
                         'eleo' : this pattern finds all repositories with 'eleo'
                                 in its name. --> chameleon

    """
    global NexusCatalog
    global project_max_len_chars

    project_max_len_chars = 0
    containing_str = ''
    if len(find_pattern) > 0:
        containing_str = ', and containing "{}"'.format(find_pattern)
    info_str = "Collecting information from Nexus with projects with org = {}".format(org_name)
    log.info("{}{}.".format(info_str, containing_str))

    try:
        r = _request_get(NEXUS3_CATALOG)
    except requests.HTTPError as excinfo:
        log.info("Fetching Nexus3 catalog. {}".format(excinfo))
        return False

    log.debug("r.status_code = {}, ok={}".format(r.status_code, r.status_code == requests.codes.ok))
    if r.status_code == requests.codes.ok:
        raw_catalog = r.text
        raw_catalog = raw_catalog.replace('"', '')
        raw_catalog = raw_catalog.replace(' ', '')
        raw_catalog = raw_catalog.replace('}', '')
        raw_catalog = raw_catalog.replace('[', '')
        raw_catalog = raw_catalog.replace(']', '')
        raw_catalog = raw_catalog.split(':')
        TmpCatalog = raw_catalog[1].split(',')
        for word in TmpCatalog:
            # Remove all projects that do not start with org_name
            if word.startswith(org_name):
                # If  a specific search string has been specified, searc = h for it
                # Empty string will match all words
                if word.find(find_pattern) >= 0:
                    # Remove onap/ from word, so we only get repository left
                    project = (org_name, word[len(org_name)+1:])
                    NexusCatalog.append(project)
                    log.debug("Added project {} to my list".format(project[1]))
                    if len(project[1]) > project_max_len_chars:
                        project_max_len_chars = len(project[1])
        log.debug("# TmpCatalog {}, NexusCatalog {}, DIFF = {}".format(
            len(TmpCatalog), len(NexusCatalog), len(TmpCatalog)-len(NexusCatalog)))
    return True
