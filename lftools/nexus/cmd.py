# -*- code: utf-8 -*-
# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Contains functions for various Nexus tasks."""

import csv
import logging
import sys

import requests
from six.moves import configparser
import yaml

from lftools import config
from lftools.nexus import Nexus
from lftools.nexus import util

log = logging.getLogger(__name__)


def get_credentials(settings_file, url=None):
    """Return credentials for Nexus instantiation."""
    if settings_file:
        try:
            with open(settings_file, 'r') as f:
                settings = yaml.safe_load(f)
        except IOError:
            log.error('Error reading settings file "{}"'.format(settings_file))
            sys.exit(1)

        if url and set(['user', 'password']).issubset(settings):
            settings['nexus'] = url
            return settings
        elif set(['nexus', 'user', 'password']).issubset(settings):
            return settings
    elif url:
        try:
            user = config.get_setting("nexus", "username")
            password = config.get_setting("nexus", "password")
        except (configparser.NoOptionError,
                configparser.NoSectionError):
            return {"nexus": url, "user": "", "password": ""}
        return {"nexus": url, "user": user, "password": password}
    log.error('Please define a settings.yaml file, or include a url if using '
              + 'lftools.ini')
    sys.exit(1)


def get_url(settings_file):
    """Return URL from settings file, if it exists."""
    if settings_file:
        try:
            with open(settings_file, 'r') as f:
                settings = yaml.safe_load(f)
        except IOError:
            log.error('Error reading settings file "{}"'.format(settings_file))
            sys.exit(1)

        if "nexus" in settings:
            return settings["nexus"]

    return ""


def reorder_staged_repos(settings_file):
    """Reorder staging repositories in Nexus.

    NOTE: This is a hack for forcing the 'Staging Repositories' repo group
    to be in the correct reverse sorted order. There is a problem with
    Nexus where it is not doing this like it should be.
    """
    with open(settings_file, 'r') as f:
        settings = yaml.safe_load(f)

    for setting in ['nexus', 'user', 'password']:
        if not setting in settings:
            log.error('{} needs to be defined'.format(setting))
            sys.exit(1)

    _nexus = Nexus(settings['nexus'], settings['user'], settings['password'])

    try:
        repo_id = _nexus.get_repo_group('Staging Repositories')
    except LookupError as e:
        log.error("Staging repository 'Staging Repositories' cannot be found")
        sys.exit(1)

    repo_details = _nexus.get_repo_group_details(repo_id)

    sorted_repos = sorted(repo_details['repositories'], key=lambda k: k['id'], reverse=True)

    for repos in sorted_repos:
        del repos['resourceURI']
        del repos['name']

    repo_update = repo_details
    repo_update['repositories'] = sorted_repos
    del repo_update['contentResourceURI']
    del repo_update['repoType']

    _nexus.update_repo_group_details(repo_id, repo_update)


def create_repos(config_file, settings_file):
    """Create repositories as defined by configuration file.

    :arg str config: Configuration file containing repository definitions that
        will be used to create the new Nexus repositories.
    :arg str settings: Settings file containing administrative credentials and
        information.
    """
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    with open(settings_file, 'r') as f:
        settings = yaml.safe_load(f)

    for setting in ['email_domain', 'base_groupId', 'repositories']:
        if not setting in config:
            log.error('{} needs to be defined in {}'.format(setting, config_file))
            sys.exit(1)

    for setting in ['nexus', 'user', 'password']:
        if not setting in settings:
            log.error('{} needs to be defined in {}'.format(setting, settings_file))
            sys.exit(1)

    _nexus = Nexus(settings['nexus'], settings['user'], settings['password'])

    def create_nexus_perms(name, targets, email, password, extra_privs=[]):
        # Create target
        try:
            target_id = _nexus.get_target(name)
        except LookupError as e:
            target_id = _nexus.create_target(name, targets)

        # Create privileges
        privs_set = [
                'create',
                'delete',
                'read',
                'update',
            ]

        privs = {}
        for priv in privs_set:
            try:
                privs[priv] = _nexus.get_priv(name, priv)
                log.info('Creating {} privileges.'.format(priv))
            except LookupError as e:
                privs[priv] = _nexus.create_priv(name, target_id, priv)

        # Create Role
        try:
            role_id = _nexus.get_role(name)
            log.info('Creating {} role.'.format(role_id))
        except LookupError as e:
            role_id = _nexus.create_role(name, privs)

        # Create user
        try:
            _nexus.get_user(name)
            log.info('Creating {} user.'.format(name))
        except LookupError as e:
            _nexus.create_user(name, email, role_id, password, extra_privs)

    def build_repo(repo, repoId, config, base_groupId, global_privs, email_domain):
        log.info('-> Building for {}.{} in Nexus'.format(base_groupId, repo))
        groupId = '{}.{}'.format(base_groupId, repo)
        target = util.create_repo_target_regex(groupId)

        if not global_privs and not 'extra_privs' in config:
            extra_privs = []
        elif global_privs:
            extra_privs = global_privs
            if 'extra_privs' in config:
                extra_privs += config['extra_privs']
            log.info('Privileges for this repo:' + ', '.join(extra_privs))
        elif 'extra_privs' in config:
            extra_privs = config['extra_privs']
            log.info('Privileges for this repo:' + ', '.join(extra_privs))

        create_nexus_perms(
            repoId,
            [target],
            email_domain,
            config['password'],
            extra_privs)

        log.info('-> Finished successfully for {}.{}!!\n'.format(base_groupId, repo))

        if 'repositories' in config:
            for sub_repo in config['repositories']:
                sub_repo_id = "{}-{}".format(repoId, sub_repo)
                build_repo(
                    sub_repo,
                    sub_repo_id,
                    config['repositories'][sub_repo],
                    groupId,
                    extra_privs,
                    email_domain)

    log.warning('Nexus repo creation started. Aborting now could leave tasks undone!')
    if 'global_privs' in config:
        global_privs = config['global_privs']
    else:
        global_privs = []

    for repo in config['repositories']:
        build_repo(repo, repo, config['repositories'][repo],
                   config['base_groupId'], global_privs, config['email_domain'])


def search(settings_file, url, repo, pattern):
    """Return of list of images in the repo matching the pattern.

    :arg str settings_file: Path to yaml file with Nexus settings.
    :arg str url: Nexus URL. Overrides settings.yaml.
    :arg str repo: The Nexus repository to audit.
    :arg str pattern: The pattern to search for in repo.
    """
    if not url and settings_file:
        url = get_url(settings_file)
    if not url:
        log.error("ERROR: No Nexus URL provided. Please provide Nexus URL in "
                  + "settings file or with the --server parameter.")
        sys.exit(1)

    _nexus = Nexus(url)

    # Check for NoneType, remove CLI escape characters from pattern
    if not pattern:
        pattern = ""
    pattern = pattern.replace("\\", "")

    all_images = _nexus.search_images(repo, pattern)

    # Ensure all of our images has a value for each of the keys we will use
    included_keys = ["name", "version", "id"]
    images = []
    for image in all_images:
        if set(included_keys).issubset(image):
            # Keep only the keys we're using
            restricted_image = {}
            for key in included_keys:
                restricted_image[key] = image[key]
            images.append(restricted_image)
    return images


def output_images(images, csv_path=None):
    """Output a list of images to stdout, or a provided file path.

    This method expects a list of dicts with, at a minimum, "name", "version",
    and "id" fields defined in each.
    :arg list images: Images to output.
    :arg str csv_path: Path to write out csv file of matching images.
    """
    if not images:
        log.warning("{}.{} called with empty images list".format(
            __name__, sys._getframe().f_code.co_name))
        return
    count = len(images)
    included_keys = images[0].keys()

    if csv_path:
        with open(csv_path, 'wb') as out_file:
            dw = csv.DictWriter(out_file, fieldnames=included_keys,
                                quoting=csv.QUOTE_ALL)
            dw.writeheader()
            for image in images:
                dw.writerow({k: v for k, v in image.items() if
                             k in included_keys})

    for image in images:
        log.info("Name: {}\nVersion: {}\nID: {}\n\n".format(
            image["name"], image["version"], image["id"]))
    log.info("Found {} images matching the query".format(count))


def delete_images(settings_file, url, images):
    """Delete all images in a list.

    :arg str settings_file: Path to yaml file with Nexus settings.
    :arg list images: List of images to delete.
    """
    credentials = get_credentials(settings_file, url)

    _nexus = Nexus(credentials['nexus'], credentials['user'],
                   credentials['password'])

    for image in images:
        _nexus.delete_image(image)


def deploy_maven_file(nexus_url, nexus_repo_id, file_name, pom_file="",
                      group_id="", artifact_id="", packaging="", version="",
                      classifier=""):
    """Deploy a file to a Nexus maven2 repository.

    :arg str nexus_url: URL of target Nexus server.
    :arg str nexus_repo_id: Name of target Nexus repo.
    :arg str file_name: Path to file that will be uploaded to Nexus.
    :arg str pom_file: Optional path to POM file containing package info.
    :arg str group_id: The artifact's groupId. Necessary if no pom is provided.
    :arg str artifact_id: The artifact's artifactId. Necessary if no pom is
        provided.
    :arg str packaging: The artifact's packaging scheme. If not provided, this
        will be guessed based on the file's extension.
    :arg str version: The artifact's version. Necessary if no pom is provided.
    :arg str classifier: Optional Nexus classifier for the artifact.
    """
    _nexus = Nexus(nexus_url)

    if pom_file:
        files = [
            ('file', (pom_file, open(pom_file, 'rb'))),
            ('file', (file_name, open(file_name, 'rb')))
        ]
        log.debug("Files: {}".format(files))

        data = {
            'r': (None, nexus_repo_id),
            'hasPom': (None, 'true')
        }
        log.debug("Data: {}".format(data))

        request_url = "{}/artifact/maven/content".format(_nexus.baseurl)
        response = requests.post(request_url, data=data, files=files)

    else:
        packaging = util.find_packaging_from_file_name(file_name)
        log.debug("Packaging found: {}".format(packaging))

        info_dict = {}
        if packaging == "rpm":
            info_dict = util.get_info_from_rpm(file_name)
        elif packaging == "deb":
            info_dict = util.get_info_from_deb(file_name)
        if info_dict and not artifact_id:
            artifact_id = info_dict["name"]
        if info_dict and not version:
            version = info_dict["version"]

        data = {
            'r': (None, nexus_repo_id),
            'p': (None, packaging),
            'hasPom': (None, 'false')
        }

        files = {
            'file': (file_name, open(file_name, 'rb'))
        }
        log.debug("Files: {}".format(files))

        if group_id:
            data['g'] = (None, group_id)
        if artifact_id:
            data['a'] = (None, artifact_id)
        if version:
            data['v'] = (None, version)
        if classifier:
            data['c'] = (None, classifier)
        log.debug("Data: {}".format(data))

        request_url = "{}/artifact/maven/content".format(_nexus.baseurl)
        log.debug("Request URL: {}".format(request_url))
        response = requests.post(request_url, data=data, files=files)

    if response.status_code != 201:
        raise requests.HTTPError("Upload failed with the following "
                                 "error:\n{}: {}".format(response.status_code,
                                                         response.text))
    else:
        log.debug("Successfully uploaded {} to {}".format(file_name,
                                                          request_url))


def release_staging_repos(repos, nexus_url=""):
    """Release one or more staging repos.

    :arg tuple repos: A tuple containing one or more repo name strings.
    :arg str nexus_url: Optional URL of target Nexus server.
    """
    credentials = get_credentials(None, nexus_url)
    _nexus = Nexus(credentials['nexus'], credentials['user'],
                   credentials['password'])

    for repo in repos:
        data = {"data": {"stagedRepositoryIds": [repo]}}
        log.debug("Sending data: {}".format(data))
        request_url = "{}/staging/bulk/promote".format(_nexus.baseurl)
        log.debug("Request URL: {}".format(request_url))
        response = requests.post(request_url, json=data)

        if response.status_code != 201:
            raise requests.HTTPError("Release failed with the following error:"
                                     "\n{}: {}".format(response.status_code,
                                                       response.text))
        else:
            log.debug("Successfully released {}".format(str(repo)))

        request_url = "{}/staging/bulk/drop".format(_nexus.baseurl)
        log.debug("Request URL: {}".format(request_url))
        response = requests.post(request_url, json=data)

        if response.status_code != 201:
            raise requests.HTTPError("Drop failed with the following error:"
                                     "\n{}: {}".format(response.status_code,
                                                       response.text))
        else:
            log.debug("Successfully dropped {}".format(str(repo)))
