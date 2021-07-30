# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Script to insert missing values from ldap into a projects INFO.yaml."""

import datetime
import inspect
import logging
import re
import sys

import click
import ruamel.yaml
import yaml
from pygerrit2 import GerritRestAPI, HTTPBasicAuth

from lftools import config
from lftools.github_helper import prvotes
from lftools.ldap_cli import helper_yaml4info

log = logging.getLogger(__name__)


@click.group()
@click.pass_context
def infofile(ctx):
    """INFO.yaml TOOLS."""
    pass


@click.command(name="create-info-file")
@click.argument("gerrit_url", required=True)
@click.argument("gerrit_project", required=True)
@click.option("--directory", type=str, required=False, default="r", help="custom gerrit directory, eg not /r/")
@click.option("--empty", is_flag=True, required=False, help="Create info file for uncreated project.")
@click.option(
    "--tsc_approval", type=str, required=False, default="missing", help="optionally provde a tsc approval link"
)
@click.pass_context
def create_info_file(ctx, gerrit_url, gerrit_project, directory, empty, tsc_approval):
    """Create an initial INFO file.

    gerrit_project example: project/full-name
    gerrit_url example: gerrit.umbrella.com
    directory example: /gerrit/ (rather than most projects /r/)
    """
    url = "https://{}/{}".format(gerrit_url, directory)
    projectid_encoded = gerrit_project.replace("/", "%2F")
    # project name with only underscores for info file anchors.
    # project name with only dashes for ldap groups.
    project_underscored = gerrit_project.replace("/", "_")
    project_underscored = project_underscored.replace("-", "_")
    project_dashed = project_underscored.replace("_", "-")

    umbrella = gerrit_url.split(".")[1]
    match = re.search(r"(?<=\.).*", gerrit_url)
    umbrella_tld = match.group(0)

    if not empty:
        user = config.get_setting("gerrit", "username")
        pass1 = config.get_setting("gerrit", "password")
        auth = HTTPBasicAuth(user, pass1)
        rest = GerritRestAPI(url=url, auth=auth)
        access_str = "projects/{}/access".format(projectid_encoded)
        headers = {"Content-Type": "application/json; charset=UTF-8"}
        result = rest.get(access_str, headers=headers)

        if "inherits_from" in result:
            inherits = result["inherits_from"]["id"]
            if inherits != "All-Projects":
                print("    Inherits from:", inherits)
                print("Better Check this unconventional inherit")

        try:
            owner = result["local"]["refs/*"]["permissions"]["owner"]["rules"]
        except:
            print("ERROR: Check project config, no owner set!")

        for x in owner:
            match = re.search(r"[^=]+(?=,)", x)
            ldap_group = match.group(0)

    if umbrella == "o-ran-sc":
        umbrella = "oran"
    if umbrella == "opendaylight":
        umbrella = "odl"

    date = datetime.datetime.now().strftime("%Y-%m-%d")

    ldap_group = "{}-gerrit-{}-committers".format(umbrella, project_dashed)

    long_string = """---
project: '{0}'
project_creation_date: '{3}'
project_category: ''
lifecycle_state: 'Incubation'
project_lead: &{1}_{0}_ptl
    name: ''
    email: ''
    id: ''
    company: ''
    timezone: ''
primary_contact: *{1}_{0}_ptl
issue_tracking:
    type: 'jira'
    url: 'https://jira.{2}/projects/'
    key: '{0}'
mailing_list:
    type: 'groups.io'
    url: 'technical-discuss@lists.{2}'
    tag: '[]'
realtime_discussion:
    type: 'irc'
    server: 'freenode.net'
    channel: '#{1}'
meetings:
    - type: 'gotomeeting+irc'
      agenda: 'https://wiki.{2}/display/'
      url: ''
      server: 'freenode.net'
      channel: '#{1}'
      repeats: ''
      time: ''""".format(
        project_underscored, umbrella, umbrella_tld, date
    )

    tsc_string = """
tsc:
    # yamllint disable rule:line-length
    approval: '{}'
    changes:
        - type: ''
          name: ''
          link: ''
""".format(
        tsc_approval, end=""
    )
    empty_committer = """    - name: ''
      email: ''
      company: ''
      id: ''
"""
    tsc_string = inspect.cleandoc(tsc_string)
    print(long_string)
    print("repositories:")
    print("    - {}".format(gerrit_project))
    print("committers:")
    print("    - <<: *{1}_{0}_ptl".format(project_underscored, umbrella, end=""))
    if not empty:
        this = helper_yaml4info(ldap_group)
        print(this, end="")
    else:
        print(empty_committer, end="")
    print(tsc_string)


@click.command(name="get-committers")
@click.argument("file", envvar="FILE_NAME", required=True)
@click.option("--full", type=bool, required=False, help="Output name email and id for all committers in an infofile")
@click.option("--id", type=str, required=False, help="Full output for a specific LFID")
@click.pass_context
def get_committers(ctx, file, full, id):
    """Extract Committer info from INFO.yaml or LDAP dump."""
    with open(file, "r") as yaml_file:
        project = yaml.safe_load(yaml_file)

    def print_committer_info(committer, full):
        """Print committers."""
        if full:
            print("    - name: {}".format(committer["name"]))
            print("      email: {}".format(committer["email"]))
        print("      id: {}".format(committer["id"]))

    def list_committers(full, id, project):
        """List commiters from the INFO.yaml file."""
        lookup = project.get("committers", [])
        for item in lookup:
            if id:
                if item["id"] == id:
                    print_committer_info(item, full)
                    break
                else:
                    continue
            print_committer_info(item, full)

    list_committers(full, id, project)


@click.command(name="sync-committers")
@click.argument("info_file")
@click.argument("ldap_file")
@click.argument("id")
@click.option("--repo", type=str, required=False, help="repo name")
@click.pass_context
def sync_committers(ctx, id, info_file, ldap_file, repo):
    """Sync committer information from LDAP into INFO.yaml."""
    ryaml = ruamel.yaml.YAML()
    ryaml.preserve_quotes = True
    ryaml.indent(mapping=4, sequence=6, offset=4)
    ryaml.explicit_start = True
    with open(info_file, "r") as stream:
        try:
            yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    with open(info_file) as f:
        info_data = ryaml.load(f)
    with open(ldap_file) as f:
        ldap_data = ryaml.load(f)

    def readfile(data, ldap_data, id):
        committer_info = info_data["committers"]
        repo_info = info_data["repositories"]
        committer_info_ldap = ldap_data["committers"]
        readldap(id, ldap_file, committer_info, committer_info_ldap, repo, repo_info)

    def readldap(id, ldap_file, committer_info, committer_info_ldap, repo, repo_info):
        for idx, val in enumerate(committer_info):
            committer = info_data["committers"][idx]["id"]
            if committer == id:
                print("{} is alread in {}".format(id, info_file))
                exit()

        for idx, val in enumerate(committer_info_ldap):
            committer = ldap_data["committers"][idx]["id"]
            if committer == id:
                name = ldap_data["committers"][idx]["name"]
                email = ldap_data["committers"][idx]["email"]
                formatid = ldap_data["committers"][idx]["id"]
                company = ldap_data["committers"][idx]["company"]
                timezone = ldap_data["committers"][idx]["timezone"]
        try:
            name
        except NameError:
            print("{} does not exist in {}".format(id, ldap_file))
            exit()

        user = ruamel.yaml.comments.CommentedMap(
            (("name", name), ("company", company), ("email", email), ("id", formatid), ("timezone", timezone))
        )

        info_data["repositories"][0] = repo
        committer_info.append(user)

        with open(info_file, "w") as f:
            ryaml.dump(info_data, f)

    readfile(info_data, ldap_data, id)


@click.command(name="check-votes")
@click.argument("info_file")
@click.argument("endpoint", type=str)
@click.argument("change_number", type=int)
@click.option("--tsc", type=str, required=False, help="path to TSC INFO file")
@click.option("--github_repo", type=str, required=False, help="Provide github repo to Check against a Github Change")
@click.pass_context
def check_votes(ctx, info_file, endpoint, change_number, tsc, github_repo):
    """Check votes on an INFO.yaml change.

    Check for Majority of votes on a gerrit or github patchset
    which changes an INFO.yaml file.

    For Gerrit endpoint is the gerrit url
    For Github the enpoint is the organization name

    Examples:
    lftools infofile check-votes /tmp/test/INFO.yaml lfit-sandbox 18 --github_repo test

    lftools infofile check-votes ~/lf/allrepos/onosfw/INFO.yaml https://gerrit.opnfv.org/gerrit/ 67302

    """

    def main(ctx, info_file, endpoint, change_number, tsc, github_repo, majority_of_committers):
        """Function so we can iterate into TSC members after commiter vote has happend."""
        with open(info_file) as file:
            try:
                info_data = yaml.safe_load(file)
            except yaml.YAMLError as exc:
                log.error(exc)

        committer_info = info_data["committers"]
        info_committers = []

        info_change = []

        if github_repo:
            id = "github_id"
            githubvotes = prvotes(endpoint, github_repo, change_number)
            for vote in githubvotes:
                info_change.append(vote)

        else:
            id = "id"
            rest = GerritRestAPI(url=endpoint)
            changes = rest.get("changes/{}/reviewers".format(change_number))
            for change in changes:
                line = (change["username"], change["approvals"]["Code-Review"])
                if "+1" in line[1] or "+2" in line[1]:
                    info_change.append(change["username"])

        for count, item in enumerate(committer_info):
            committer = committer_info[count][id]
            info_committers.append(committer)

        have_not_voted = [item for item in info_committers if item not in info_change]
        have_not_voted_length = len(have_not_voted)
        have_voted = [item for item in info_committers if item in info_change]
        have_voted_length = len(have_voted)
        log.info("Number of Committers:")
        log.info(len(info_committers))
        committer_length = len(info_committers)
        log.info("Committers that have voted:")
        log.info(have_voted)
        log.info(have_voted_length)
        log.info("Committers that have not voted:")
        log.info(have_not_voted)
        log.info(have_not_voted_length)

        if have_voted_length == 0:
            log.info("No one has voted:")
            sys.exit(1)

        if have_voted_length != 0:
            majority = have_voted_length / committer_length
            if majority >= 0.5:
                log.info("Majority committer vote reached")
                if tsc:
                    log.info("Need majority of tsc")
                    info_file = tsc
                    majority_of_committers += 1
                    if majority_of_committers == 2:
                        log.info("TSC majority reached auto merging commit")
                    else:
                        main(ctx, info_file, endpoint, change_number, tsc, github_repo, majority_of_committers)
            else:
                log.info("majority not yet reached")
                sys.exit(1)

    majority_of_committers = 0
    main(ctx, info_file, endpoint, change_number, tsc, github_repo, majority_of_committers)


infofile.add_command(get_committers)
infofile.add_command(sync_committers)
infofile.add_command(check_votes)
infofile.add_command(create_info_file)
