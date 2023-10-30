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
import re
import sys
import xml.etree.ElementTree as et  # nosec
from time import sleep

import bs4
import requests
import yaml
from six.moves import configparser

from lftools import config
from lftools.nexus import Nexus, util

log = logging.getLogger(__name__)


def get_credentials(settings_file, url=None):
    """Return credentials for Nexus instantiation."""

    if settings_file:
        try:
            with open(settings_file, "r") as f:
                settings = yaml.safe_load(f)
        except IOError:
            log.error('Error reading settings file "{}"'.format(settings_file))
            sys.exit(1)

        if url and set(["user", "password"]).issubset(settings):
            settings["nexus"] = url
            return settings
        elif set(["nexus", "user", "password"]).issubset(settings):
            return settings
    elif url:
        try:
            auth_url = url.replace("https://", "")
            user = config.get_setting(auth_url, "username")
            password = config.get_setting(auth_url, "password")
        except (configparser.NoOptionError, configparser.NoSectionError):
            log.info("Failed to get nexus credentials; using empty username " "and password.")
            return {"nexus": url, "user": "", "password": ""}
        return {"nexus": url, "user": user, "password": password}
    log.error("Please define a settings.yaml file, or include a url if using " + "lftools.ini")
    sys.exit(1)


def get_url(settings_file):
    """Return URL from settings file, if it exists."""
    if settings_file:
        try:
            with open(settings_file, "r") as f:
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
    with open(settings_file, "r") as f:
        settings = yaml.safe_load(f)

    for setting in ["nexus", "user", "password"]:
        if setting not in settings:
            log.error("{} needs to be defined".format(setting))
            sys.exit(1)

    _nexus = Nexus(settings["nexus"], settings["user"], settings["password"])

    try:
        repo_id = _nexus.get_repo_group("Staging Repositories")
    except LookupError:
        log.error("Staging repository 'Staging Repositories' cannot be found")
        sys.exit(1)

    repo_details = _nexus.get_repo_group_details(repo_id)

    sorted_repos = sorted(repo_details["repositories"], key=lambda k: k["id"], reverse=True)

    for repos in sorted_repos:
        del repos["resourceURI"]
        del repos["name"]

    repo_update = repo_details
    repo_update["repositories"] = sorted_repos
    del repo_update["contentResourceURI"]
    del repo_update["repoType"]

    _nexus.update_repo_group_details(repo_id, repo_update)


def create_repos(config_file, settings_file, url):
    """Create repositories as defined by configuration file.

    :arg str config_file: Configuration file containing repository definitions that
        will be used to create the new Nexus repositories.
    :arg str settings: Settings file containing administrative credentials and
        information.
    :arg str url: url in the format https:// user nad password will be taken from lftools
    if url is provided.
    """
    if not settings_file:
        from lftools import config

        settings_url = url.replace("https://", "")
        password = config.get_setting(settings_url, "password")
        username = config.get_setting(settings_url, "username")

    with open(config_file, "r") as f:
        config = yaml.safe_load(f)
    if settings_file:
        with open(settings_file, "r") as f:
            settings = yaml.safe_load(f)

    for setting in ["email_domain", "base_groupId", "repositories"]:
        if setting not in config:
            log.error("{} needs to be defined in {}".format(setting, config_file))
            sys.exit(1)

    if settings_file:
        for setting in ["nexus", "user", "password"]:
            if setting not in settings:
                log.error("{} needs to be defined in {}".format(setting, settings_file))
                sys.exit(1)

    if settings_file:
        _nexus = Nexus(settings["nexus"], settings["user"], settings["password"])
    else:
        _nexus = Nexus(url, username, password)

    def create_nexus_perms(name, targets, email, password, extra_privs=[]):
        # Create target
        try:
            target_id = _nexus.get_target(name)
        except LookupError:
            target_id = _nexus.create_target(name, targets)

        # Create privileges
        privs_set = [
            "create",
            "delete",
            "read",
            "update",
        ]

        privs = {}
        for priv in privs_set:
            try:
                privs[priv] = _nexus.get_priv(name, priv)
                log.info("Creating {} privileges.".format(priv))
            except LookupError:
                privs[priv] = _nexus.create_priv(name, target_id, priv)

        # Create Role
        try:
            role_id = _nexus.get_role(name)
            log.info("Role {} already exists.".format(role_id))
        except LookupError:
            role_id = _nexus.create_role(name, privs)

        # Create user
        try:
            _nexus.get_user(name)
            log.info("User {} already exists.".format(name))
        except LookupError:
            _nexus.create_user(name, email, role_id, password, extra_privs)

    def build_repo(repo, repoId, config, base_groupId, global_privs, email_domain, strict=True):
        log.info("-> Building for {}.{} in Nexus".format(base_groupId, repo))
        groupId = "{}.{}".format(base_groupId, repo)
        target = util.create_repo_target_regex(groupId, strict)

        if not global_privs and "extra_privs" not in config:
            extra_privs = []
        elif global_privs:
            extra_privs = global_privs
            if "extra_privs" in config:
                extra_privs += config["extra_privs"]
            log.info("Privileges for this repo:" + ", ".join(extra_privs))
        elif "extra_privs" in config:
            extra_privs = config["extra_privs"]
            log.info("Privileges for this repo:" + ", ".join(extra_privs))

        create_nexus_perms(repoId, [target], email_domain, config["password"], extra_privs)

        log.info("-> Finished successfully for {}.{}!!\n".format(base_groupId, repo))

        if "repositories" in config:
            for sub_repo in config["repositories"]:
                sub_repo_id = "{}-{}".format(repoId, sub_repo)
                build_repo(sub_repo, sub_repo_id, config["repositories"][sub_repo], groupId, extra_privs, email_domain)

    log.warning("Nexus repo creation started. Aborting now could leave tasks undone!")
    if "global_privs" in config:
        global_privs = config["global_privs"]
    else:
        global_privs = []
    if "strict_url_regex" in config:
        strict = config["strict_url_regex"]
    else:
        strict = True

    for repo in config["repositories"]:
        build_repo(
            repo,
            repo,
            config["repositories"][repo],
            config["base_groupId"],
            global_privs,
            config["email_domain"],
            strict,
        )


def create_roles(config_file, settings_file):
    """Create Nexus roles as defined by configuration file.

    :arg str config: Configuration file containing role definitions that
        will be used to create the new Nexus roles.
    :arg str settings: Settings file containing administrative credentials and
        information.
    """
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    with open(settings_file, "r") as f:
        settings = yaml.safe_load(f)

    for setting in ["nexus", "user", "password"]:
        if setting not in settings:
            log.error("{} needs to be defined in {}".format(setting, settings_file))
            sys.exit(1)

    _nexus = Nexus(settings["nexus"], settings["user"], settings["password"])

    required_settings = ["name", "roles"]
    for role in config:
        for setting in required_settings:
            if setting not in config[role]:
                log.error(
                    "{} not defined for role {}. Please ensure that {} "
                    "are defined for each role in {}".format(setting, role, required_settings, config_file)
                )
                sys.exit(1)

        subrole_ids = []
        for subrole in config[role]["roles"]:
            subrole_id = _nexus.get_role(subrole)
            subrole_ids.append(subrole_id)
        config[role]["roles"] = subrole_ids

        if "description" not in config[role]:
            config[role]["description"] = config[role]["name"]

        if "privileges" in config[role]:
            priv_ids = []
            for priv in config[role]["privileges"]:
                priv_ids.append(_nexus.get_priv_by_name(priv))
            config[role]["privileges"] = priv_ids
        else:
            config[role]["privileges"] = []

    for role in config:
        _nexus.create_role(
            config[role]["name"], config[role]["privileges"], role, config[role]["description"], config[role]["roles"]
        )


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
        log.error(
            "ERROR: No Nexus URL provided. Please provide Nexus URL in "
            + "settings file or with the --server parameter."
        )
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
        log.warning("{}.{} called with empty images list".format(__name__, sys._getframe().f_code.co_name))
        return
    count = len(images)
    included_keys = images[0].keys()

    if csv_path:
        with open(csv_path, "wb") as out_file:
            dw = csv.DictWriter(out_file, fieldnames=included_keys, quoting=csv.QUOTE_ALL)
            dw.writeheader()
            for image in images:
                dw.writerow({k: v for k, v in image.items() if k in included_keys})

    for image in images:
        log.info("Name: {}\nVersion: {}\nID: {}\n\n".format(image["name"], image["version"], image["id"]))
    log.info("Found {} images matching the query".format(count))


def delete_images(settings_file, url, images):
    """Delete all images in a list.

    :arg str settings_file: Path to yaml file with Nexus settings.
    :arg list images: List of images to delete.
    """
    credentials = get_credentials(settings_file, url)

    _nexus = Nexus(credentials["nexus"], credentials["user"], credentials["password"])

    for image in images:
        _nexus.delete_image(image)


def get_activity_text(act):
    """Concatenate the Value strings in the XML data and return it.

    <stagingActivityEvent>
        <timestamp>2019-10-18T09:39:24.841Z</timestamp>
        <name>ruleFailed</name>
        <severity>1</severity>
        <properties>
            <stagingProperty>
                <name>typeId</name>
                <value>javadoc-staging</value>
            </stagingProperty>
            <stagingProperty>
                <name>failureMessage</name>
                <value>
                    Missing: no javadoc jar found in folder '/org/opendaylight/odlparent/leveldbjni-all/6.0.1'
                </value>
            </stagingProperty>
        </properties>
    </stagingActivityEvent>
    """
    tmp_list = []
    act_soup = bs4.BeautifulSoup(str(act), "xml")
    stagingProperties = act_soup.find_all("stagingProperty")
    for stagingProperty in stagingProperties:
        value = stagingProperty.find("value")
        tmp_list.append(value.text)
    txt_str = " --> ".join(map(str, tmp_list))
    return txt_str


def add_str_if_not_exist(new_str, existing_str_lst):
    """Will return True if the new string provided is not already in the list of strings."""
    addthis = True
    for fail2txt in existing_str_lst:
        if new_str.text in fail2txt:
            addthis = False
    return addthis


def find_release_time(events):
    """Returns the time when a repository was released, or None if it has not been released yet."""
    for event in events:
        name = event.find("name")
        stopped = event.find("stopped")
        if name.text == "release" and stopped is not None:
            return stopped.text
    return None


def release_staging_repos(repos, verify, nexus_url=""):
    """Release one or more staging repos.

    :arg tuple repos: A tuple containing one or more repo name strings.
    :arg str nexus_url: Optional URL of target Nexus server.
    :arg flag --verify-only: Only verify repo and exit.
    """
    credentials = get_credentials(None, nexus_url)
    _nexus = Nexus(credentials["nexus"], credentials["user"], credentials["password"])

    for repo in repos:
        # Verify repo before releasing
        activity_url = "{}/staging/repository/{}/activity".format(_nexus.baseurl, repo)
        log.info("Request URL: {}".format(activity_url))
        response = requests.get(activity_url, auth=_nexus.auth)

        if response.status_code != 200:
            raise requests.HTTPError(
                "Verification of repo failed with the following error:"
                "\n{}: {}".format(response.status_code, response.text)
            )

        soup = bs4.BeautifulSoup(response.text, "xml")
        values = soup.find_all("value")
        activities = soup.find_all("stagingActivityEvent")
        failures = []
        failures2 = []
        successes = []
        is_repo_closed = []

        for act in activities:
            # Check for failures
            if re.search("ruleFailed", act.text):
                failures2.append(get_activity_text(act))
            if re.search("repositoryCloseFailed", act.text):
                failures2.append(get_activity_text(act))
            # Check if already released
            if re.search("repositoryReleased", act.text):
                successes.append(get_activity_text(act))
            # Check if already Closed
            if re.search("repositoryClosed", act.text):
                is_repo_closed.append(get_activity_text(act))

        # Check for other failures (old code part). only add them if not already there
        # Should be possible to remove this part, but could not find a sample XML with these values.
        for message in values:
            if re.search("StagingRulesFailedException", message.text):
                if add_str_if_not_exist(message, failures2):
                    failures.append(message.text)
            if re.search("Invalid", message.text):
                if add_str_if_not_exist(message, failures2):
                    failures.append(message.text)

        # Start check result
        if len(failures) != 0 or len(failures2) != 0:
            log.info("\n".join(map(str, failures2)))
            log.info("\n".join(map(str, failures)))
            log.info("One or more rules failed")
            sys.exit(1)
        else:
            log.info("PASS: No rules have failed")

        if len(successes) != 0:
            log.info("\n".join(map(str, successes)))
            log.info("Nothing to do: Repository already released")
            sys.exit(0)

        if len(is_repo_closed) == 0:
            log.info(is_repo_closed)
            log.info("Repository is not in closed state")
            sys.exit(1)
        else:
            log.info("PASS: Repository {} is in closed state".format(is_repo_closed[0]))

        log.info("Successfully verified {}".format(str(repo)))

    if not verify:
        log.info("running release")
        for repo in repos:
            data = {"data": {"stagedRepositoryIds": [repo]}}
            log.info("Sending data: {}".format(data))
            request_url = "{}/staging/bulk/promote".format(_nexus.baseurl)
            log.info("Request URL: {}".format(request_url))
            log.info("Requesting Nexus to release {}".format(repo))

            response = requests.post(request_url, json=data, auth=_nexus.auth)

            if response.status_code != 201:
                raise requests.HTTPError(
                    "Release failed with the following error:" "\n{}: {}".format(response.status_code, response.text)
                )
            else:
                log.info("Nexus is now working on releasing {}".format(str(repo)))

            # Hang out until the repo is fully released
            log.info("Waiting for Nexus to complete releasing {}".format(str(repo)))
            wait_seconds = 20
            wait_iteration = 0
            consecutive_failures = 0
            activity_url = "{}/staging/repository/{}/activity".format(_nexus.baseurl, repo)
            sleep(5)  # Quick sleep to allow small repos to release.
            while True:
                try:
                    response = requests.get(activity_url, auth=_nexus.auth).text
                    consecutive_failures = 0
                    root = et.fromstring(response)  # nosec
                    time = find_release_time(root.findall("./stagingActivity"))
                    if time is not None:
                        log.info("Repo released at: {}".format(time))
                        break

                except requests.exceptions.ConnectionError as e:
                    # Ignore failures unless they pile up. We do this because we seem to be facing transient
                    # issues (like DNS failures) and completing repository release here is absolutely critical,
                    # as otherwise this can lead to failing to perform post-release steps, which cannot be
                    # manually recovered.
                    consecutive_failures += 1
                    if consecutive_failures > 50:
                        raise e
                    log.warn(e, stack_info=True, exc_info=True)

                sleep(wait_seconds)
                wait_iteration += 1
                log.info("Still waiting... {:>4d} seconds gone".format(wait_seconds * wait_iteration))
