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
"""Set of functions to facilitate copying nexus release images to docker.

 Workflow if you do it manually
    docker pull nexus3.onap.org:10002/onap/aaf/aaf_hello:2.1.3
    docker images --> imageid --> 991170554e6e
    docker tag 991170554e6e onap/aaf-aaf_hello:2.1.3
    docker push onap/aaf-aaf_hello:2.1.3
    docker image rm --force 991170554e6e

Filter
Find all projects that starts with MAIN_PART and contains FindProject.

Set MAIN_PART to the common beginning of the project name.
    MAIN_PART = onap --> find all projects starting with onap

Set the FindProject to "" to find all projects that starts with MAIN_PART

Set the FindProject to a str to find all projects that contains that string
  and starts with MAIN_PART
    FindProject = "aaf_co"   # onap/aaf/aaf_config,onap/aaf/aaf_core
    FindProject = "aaf_cm"   # onap/aaf/aaf_cm
    FindProject = "aa"
    FindProject = ""        # Find all projects

lftools nexus docker
"""
from __future__ import print_function

import logging
import multiprocessing
from multiprocessing.dummy import Pool as ThreadPool
import re
import socket
import sys

import docker
import requests
from tqdm import tqdm
import urllib3

log = logging.getLogger(__name__)

NEXUS3_BASE = "https://nexus3.onap.org:10002"
NEXUS3_CATALOG = NEXUS3_BASE + "/v2/_catalog"

NEXUS3_PROJ_NAME_HEADER = "Nexus3 Project Name"
DOCKER_PROJ_NAME_HEADER = "Docker Project Name"

NexusCatalog = []
projects = []
TotTagsToBeCopied = 0


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


class TagClass:
    """Base class for nexus and docker tag class.

    This class contains the actual valid and invalid tags for a repository,
    as well as an indication if the repository exist or not.

    A valid tag has the following format #.#.# (1.2.3, or 1.22.333)

    Parameter:
        org_name     : The organization part of the repository.
            'onap'

        repo_name : The nexus repository name
            'aaf/aaf_service'
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

    This class fetches and stores all nexus tags for a repository.

    Doing this manually from command line, you will give this command:
        curl -s https://nexus3.onap.org:10002/v2/onap/aaf/aaf_service/tags/list
    which gives you the following output:
        {"name":"onap/aaf/aaf_service","tags":["2.1.1","2.1.3","2.1.4","2.1.5","2.1.6","2.1.7","2.1.8"]}

    When we fetch the tags from the nexus repository url, they are returned like
        {"name":"onap/aaf/aaf_service","tags":["2.1.1","2.1.3","2.1.4","2.1.5"]}
    Hence, we need to extract all the tags, and add them to our list of valid or
    invalid tags.
    If we fail to collect the tags, we set the repository_exist flag to false.

    Parameter:
        org_name     : The organization part of the repository.
            'onap'

        repo_name : The nexus repository name
            'aaf/aaf_service'

    Result:
        Will fetch all tags from the Nexus Repository URL, and store each tag
        in self.valid or self.invalid as a list.
        If no repository is found, self.repository_exist will be set to False.
    """

    def __init__(self, org_name, repo_name):
        """Initialize this class."""
        TagClass.__init__(self, org_name, repo_name)
        log.debug("Fetching nexus tags for {}/{}".format(org_name, repo_name))
        r = requests.get(NEXUS3_BASE + "/v2/" + org_name + "/" + repo_name + "/tags/list")
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
        org_name     : The organization part of the repository.
            'onap'

        repo_name : The docker repository name
            'base_sdc-sanity'

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
        r = requests.get(self._docker_base + "/" + org_name + "/" + repo_name + "/tags")
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
    nexus to docker.

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
        """Implement sort order base on nexus repo name."""
        return self.nexus_repo_name < other.nexus_repo_name

    def calc_nexus_project_name(self):
        """Get nexus project name."""
        return self.org_name + "/" + self.nexus_repo_name

    def calc_docker_project_name(self):
        """Get docker project name."""
        return self.org_name + "/" + self.docker_repo_name

    def _set_docker_repo_name(self, nexus_repo_name):
        """Set docker repo name.

        Docker repository will be based on the nexus repo name.
        But replacing all '/' with '-'
        """
        self.docker_repo_name = self.nexus_repo_name.replace('/', '-')
        log.debug("ProjName = {} ---> Docker name = {}".format(
            self.nexus_repo_name, self.docker_repo_name))

    def _populate_tags_to_copy(self):
        """Populate tags_to_copy list.

        Check that all valid nexus tags are among the docker valid tags.
        If not, add them to the tags_2_copy list.
        """
        log.debug('Populate {} has valid nexus {} and valid docker {}'.format(
            self.docker_repo_name,
            len(self.nexus_tags.valid), len(self.docker_tags.valid)))

        if len(self.nexus_tags.valid) > 0:
            for nexustag in self.nexus_tags.valid:
                if not nexustag in self.docker_tags.valid:
                    log.debug('Need to copy tag {} from {}'.format(nexustag, self.docker_repo_name))
                    self.tags_2_copy.add_tag(nexustag)

    def _pull_tag_push_msg(self, info_text, count, retry_text=''):
        """Print a formated message using log.info."""
        due_to_txt = ''
        if len(retry_text) > 0:
            due_to_txt = 'due to {}'.format(retry_text)

        b4_txt_template = 'Attempt {}: '
        b4_txt = ''.ljust(len(b4_txt_template)-1)
        if count > 1:
            b4_txt = b4_txt_template.format(count)
        log.info("{}: {} {}".format(b4_txt, info_text, due_to_txt))

    def _docker_pull(self, nexus_image_str, count, tag, retry_text=''):
        """Pull an image from Nexus."""
        self._pull_tag_push_msg('Pulling   nexus  image {} with tag {}'.format(
            self.calc_nexus_project_name(), tag), count, retry_text)
        image = self.docker_client.images.pull(nexus_image_str)
        return image

    def _docker_tag(self, count, image, tag, retry_text=''):
        """Tag the image with proper docker name and version."""
        self._pull_tag_push_msg('Creating  docker image {} with tag {}'.format(
            self.calc_docker_project_name(), tag), count, retry_text)
        image.tag(self.calc_docker_project_name(), tag=tag)

    def _docker_push(self, count, image, tag, retry_text):
        """Push the docker image to docker hub."""
        self._pull_tag_push_msg('Pushing   docker image {} with tag {}'.format(
            self.calc_docker_project_name(), tag), count, retry_text)
        self.docker_client.images.push(self.calc_docker_project_name(), tag=tag)

    def _docker_cleanup(self, count, image, tag, retry_text=''):
        """Remove the local copy of the image."""
        image_id = _format_image_id(image.short_id)
        self._pull_tag_push_msg('Cleanup   docker image {} with tag {} and id {}'.format(
            self.calc_docker_project_name(), tag, image_id), count, retry_text)
        self.docker_client.images.remove(image.id, force=True)

    def docker_pull_tag_push(self):
        """Copy all missing docker images from Nexus.

        This is the main function which will copy a specific tag from nexus
        to Docker repository.

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
                            image = self._docker_pull(nexus_image_str, cnt_break_loop, tag, retry_text)
                            break

                        if stage == 'tag':
                            self._docker_tag(cnt_break_loop, image, tag, retry_text)
                            break

                        if stage == 'push':
                            self._docker_push(cnt_break_loop, image, tag, retry_text)
                            break

                        if stage == 'cleanup':
                            self._docker_cleanup(cnt_break_loop, image, tag, retry_text)
                            break
                    except socket.timeout:
                        retry_text = 'Socket Timeout'
                    except requests.exceptions.ConnectionError:
                        retry_text = 'Connection Error'
                    except urllib3.exceptions.ReadTimeoutError:
                        retry_text = 'Read Timeout Error'
                    except:
                        retry_text = "Unexpected error. {}".format(sys.exc_info()[0])
                    cnt_break_loop = cnt_break_loop + 1
                    if (cnt_break_loop > 10):
                        raise requests.HTTPError(retry_text)


def get_nexus3_catalog(org_name='onap', find_pattern=''):
    """Main function to collect all nexus projects.

    This function will collect the Nexus catalog for all projects starting with
    'org_name' as well as containing a pattern if specified.

    If you do it manually, you give the following command.
        curl -s https://nexus3.onap.org:10002/v2/_catalog

    which gives you the following output.
        {"repositories":["dcae_dmaapbc","onap/aaf/aaf-base-openssl_1.1.0",
        "onap/aaf/aaf-base-xenial","onap/aaf/aaf_agent","onap/aaf/aaf_cass",
        "onap/aaf/aaf_cm","onap/aaf/aaf_config","onap/aaf/aaf_core"]}


    Parameters:
        org_name     : Organizational name, default set to 'onap'
            Nexus catalog starts with <org_name>/<project name>

        find_pattern : A pattern, that if specified, needs to be in part of the
                        project name.
                        for instance,
                         ''    : this pattern finds all projects.
                         'eleo' : this pattern finds all project names with 'aaf'
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
    r = requests.get(NEXUS3_CATALOG)
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




def fetch_all_tags():
    """Fetch all tags function.

    This function will use multiprocess to fetch all tags for all projects in NexusCatalog.
    """

    NbrProjects = len(NexusCatalog)
    log.info("Fetching tags from Nexus and Docker for {} projects".format(NbrProjects))
    pbar = tqdm(total=NbrProjects)

    def _fetch_all_tags(proj):
        """Helper function for multiprocessing.

        This function, will create an instance of ProjectClass (which triggers
        the project class fetching all nexus/docker tags)
        Then adding this instance to the project list.

            Parameters:
                proj : Tuple with 'org' and 'repo'
                    ('onap', 'aaf/aaf_service')
        """
        new_proj = ProjectClass(proj)
        projects.append(new_proj)
        pbar.update(1)

    pool = ThreadPool(multiprocessing.cpu_count())
    pool.map(_fetch_all_tags, NexusCatalog)
    pool.close()
    pool.join()

    pbar.close()
    projects.sort()


def copy_from_nexus_to_docker():
    """Copy all missing tags.

    This function will use multiprocess to copy all missing tags in the project list.
    """

    _tot_tags = 0
    for proj in projects:
        _tot_tags = _tot_tags + len(proj.tags_2_copy.valid)
    pbar = tqdm(total=_tot_tags)

    def _docker_pull_tag_push(proj):
        """Helper function for multiprocessing.

        This function, will call the ProjectClass proj's docker_pull_tag_push.

            Parameters:
                proj : Tuple with 'org' and 'repo'
                    ('onap', 'aaf/aaf_service')
        """
        proj.docker_pull_tag_push()
        pbar.update(len(proj.tags_2_copy.valid))

    pool = ThreadPool(multiprocessing.cpu_count())
    pool.map(_docker_pull_tag_push, projects)
    pool.close()
    pool.join()

    pbar.close()


def print_tags_header(header_str, col_1_str):
    """Print simple header."""
    fmt_str = '{:<'+str(project_max_len_chars)+'} : '
    print(header_str)
    print(fmt_str.format(col_1_str), end='')
    print('Tags')
    print('-'*project_max_len_chars*2)


def print_tags_data(proj_name, tags):
    """Print tag data."""
    fmt_str = '{:<'+str(project_max_len_chars)+'} : '
    if len(tags) > 0:
        print(fmt_str.format(proj_name), end='')
        tag_i = 0
        for tag in tags:
            if tag_i > 0:
                print(", ", end='')
            print(tag, end='')
            tag_i = tag_i + 1
        print("")


def print_nexus_valid_tags():
    """Print Nexus valid tags."""
    print_tags_header("Nexus Valid Tags", NEXUS3_PROJ_NAME_HEADER)
    for proj in projects:
        print_tags_data(proj.nexus_repo_name, proj.nexus_tags.valid)
    print("")


def print_nexus_invalid_tags():
    """Print Nexus invalid tags."""
    print_tags_header("Nexus InValid Tags", NEXUS3_PROJ_NAME_HEADER)
    for proj in projects:
        print_tags_data(proj.nexus_repo_name, proj.nexus_tags.invalid)
    print("")


def print_docker_valid_tags():
    """Print Docker valid tags."""
    print_tags_header("Docker Valid Tags", DOCKER_PROJ_NAME_HEADER)
    for proj in projects:
        print_tags_data(proj.docker_repo_name, proj.docker_tags.valid)
    print("")


def print_docker_invalid_tags():
    """Print Docker invalid tags."""
    print_tags_header("Docker InValid Tags", DOCKER_PROJ_NAME_HEADER)
    for proj in projects:
        print_tags_data(proj.docker_repo_name, proj.docker_tags.invalid)
    print("")


def print_stats():
    """Print simple repo/tag statistics."""
    print_tags_header("Tag statistics (V=Valid, I=InValid)", NEXUS3_PROJ_NAME_HEADER)
    fmt_str = '{:<'+str(project_max_len_chars)+'} : '
    for proj in projects:
        print("{}Nexus V:{} I:{} -- Docker V:{} I:{}".format(
            fmt_str.format(proj.nexus_repo_name),
            len(proj.nexus_tags.valid),
            len(proj.nexus_tags.invalid),
            len(proj.docker_tags.valid),
            len(proj.docker_tags.invalid)))
    print("")


def print_missing_docker_proj():
    """Print missing docker repos."""
    print("Missing corresponding Docker Project")
    fmt_str = '{:<'+str(project_max_len_chars)+'} : '
    print(fmt_str.format(NEXUS3_PROJ_NAME_HEADER), end='')
    print(DOCKER_PROJ_NAME_HEADER)
    print('-'*project_max_len_chars*2)
    for proj in projects:
        if not proj.docker_tags.repository_exist:
            print(fmt_str.format(proj.nexus_repo_name), end='')
            print(proj.docker_project_name)
    print("")


def print_nexus_tags_2_copy():
    """Print tags that needs to be copied."""
    print("Nexus project tags to copy to docker")
    fmt_str = '{:<'+str(project_max_len_chars)+'} : '
    print(fmt_str.format(NEXUS3_PROJ_NAME_HEADER), end='')
    print("Tags to copy")
    print('-'*project_max_len_chars*2)
    for proj in projects:
        if len(proj.tags_2_copy.valid) > 0:
            tag_i = 0
            print(fmt_str.format(proj.nexus_repo_name), end='')
            for tag in proj.tags_2_copy.valid:
                if tag_i > 0:
                    print(", ", end='')
                print(tag, end='')
                tag_i = tag_i + 1
            print("")
    print("")


def start_point(org_name, find_pattern='', summary=True, verbose=False, copy=False):
    """Main function."""
    get_nexus3_catalog(org_name, find_pattern)
    fetch_all_tags()
    if verbose:
        print_nexus_valid_tags()
        print_nexus_invalid_tags()
        print_docker_valid_tags()
        print_docker_invalid_tags()
        print_stats()
    if summary or verbose:
        print_missing_docker_proj()
        print_nexus_tags_2_copy()
    if copy:
        log.info("About to copy, but it is disabled")
        if 1 == 2:
            copy_from_nexus_to_docker()
