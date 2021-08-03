# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2018 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Test nexus command."""

import os
import re

import pytest

from lftools.nexus import cmd, util

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures")


@pytest.fixture
def mock_get_credentials(mocker):
    rtn = {"nexus": "http://nexus.localhost", "user": "user", "password": "password"}
    mocker.patch("lftools.nexus.cmd.get_credentials", return_value=rtn)
    mocker.patch("time.sleep", return_value=True)


@pytest.fixture
def nexus2_obj_create(responses):
    """Create the proper responses for the init of a nexus object"""
    baseurl_endpoint = re.compile(".*nexus.*/service/local/repo_targets")
    responses.add(responses.GET, baseurl_endpoint, status=200)


@pytest.mark.datafiles(os.path.join(FIXTURE_DIR, "nexus"))
def test_create_roles(datafiles, responses, nexus2_obj_create):
    """Test create_roles() method with good config."""
    os.chdir(str(datafiles))
    baseurl = "http://nexus.localhost/service/local/"
    roles_url = baseurl + "roles"
    privs_url = baseurl + "privileges"
    role1_return = """{"data": {"id": "lf-deployment"}}"""
    role2_return = """{"data": {"id": "LF Deployment By Name"}}"""

    for _ in range(4):  # Add response for each expected "get_role" call
        with open("simplified_roles_list.json", "r") as roles_return:
            responses.add(responses.GET, roles_url, roles_return.read())
    for _ in range(2):  # Add response for each expected "get_priv" call
        with open("simplified_privs_list.json", "r") as privs_return:
            responses.add(responses.GET, privs_url, privs_return.read())
    responses.add(responses.POST, roles_url, role1_return, status=201)
    responses.add(responses.POST, roles_url, role2_return, status=201)

    cmd.create_roles("role_config-good.yaml", "settings.yaml")


@pytest.mark.datafiles(os.path.join(FIXTURE_DIR, "nexus"))
def test_release_staging_repos(datafiles, responses, nexus2_obj_create, mock_get_credentials):
    """Test create_roles() method with good config."""
    os.chdir(str(datafiles))
    baseurl = "http://nexus.localhost/service/local"
    repos = ["test-release-repo"]
    activity_url = "{}/staging/repository/{}/activity".format(baseurl, repos[0])
    request_url = "{}/staging/bulk/promote".format(baseurl)

    closed_return = open("staging_activities_closed.xml", "r").read()
    releasing_return = open("staging_activities_releasing.xml", "r").read()
    released_return = open("staging_activities_released.xml", "r").read()

    responses.add(responses.GET, activity_url, closed_return, status=200)
    responses.add(responses.POST, request_url, status=201)
    # While checking for the "release" activity, we return once without it in
    # order to exercise the code for "if not released".
    responses.add(responses.GET, activity_url, releasing_return, status=200)
    responses.add(responses.GET, activity_url, released_return, status=200)

    cmd.release_staging_repos(repos, False)


def test_create_repo_target_regex():
    """Test create_repo_target_regex() command."""

    test_url_3_par = [
        [False, "org.o-ran-sc.org", "/org/o/ran/sc/org/"],
        [
            False,
            "org.opendaylight.odlparent",
            "/org/opendaylight/odlparent/odlparent/4.0.0-SNAPSHOT/odlparent-4.0.0-20180424.132124-69.pom",
        ],
        [
            False,
            "org.opendaylight.honeycomb.vbd",
            "/org/opendaylight/honeycomb/vbd/odl-vbd/1.4.0-SNAPSHOT/odl-vbd-1.4.0-20180422.024456-12-features.xml",
        ],
        [False, "org.openecomp.mso", "/org/openecomp/mso/1.1.0-SNAPSHOT/mso-1.1.0-20170606.171056-26.pom"],
        [False, "org.onap.dcaegen2", "/org/onap.dcaegen2/1.2.0-SNAPSHOT/dcaegen2-1.2.0-20180403.182529-10.pom"],
        [False, "io.fd.vpp", "/io/fd/vpp/jvpp/16.06/jvpp-16.06.jar"],
        [True, "org.o-ran-sc.org", "/org/o-ran-sc/org/"],
        [True, "org.o-ran-sc.org", "/org/o-ran-sc/org/ric-plt-lib-rmr"],
        [
            True,
            "org.opendaylight.odlparent",
            "/org/opendaylight/odlparent/odlparent/4.0.0-SNAPSHOT/odlparent-4.0.0-20180424.132124-69.pom",
        ],
        [
            True,
            "org.opendaylight.honeycomb.vbd",
            "/org/opendaylight/honeycomb/vbd/odl-vbd/1.4.0-SNAPSHOT/odl-vbd-1.4.0-20180422.024456-12-features.xml",
        ],
        [True, "org.openecomp.mso", "/org/openecomp/mso/1.1.0-SNAPSHOT/mso-1.1.0-20170606.171056-26.pom"],
        [True, "org.onap.dcaegen2", "/org/onap/dcaegen2/1.2.0-SNAPSHOT/dcaegen2-1.2.0-20180403.182529-10.pom"],
        [True, "io.fd.vpp", "/io/fd/vpp/jvpp/16.06/jvpp-16.06.jar"],
    ]

    for url in test_url_3_par:
        a = util.create_repo_target_regex(url[1], url[0])
        a_regex = re.compile(a)
        assert a_regex.match(url[2]) is not None

    test_url_2_par = [
        ["org.o-ran-sc.org", "/org/o-ran-sc/org/"],
        [
            "org.opendaylight.odlparent",
            "/org/opendaylight/odlparent/odlparent/4.0.0-SNAPSHOT/odlparent-4.0.0-20180424.132124-69.pom",
        ],
        [
            "org.opendaylight.honeycomb.vbd",
            "/org/opendaylight/honeycomb/vbd/odl-vbd/1.4.0-SNAPSHOT/odl-vbd-1.4.0-20180422.024456-12-features.xml",
        ],
        ["org.openecomp.mso", "/org/openecomp/mso/1.1.0-SNAPSHOT/mso-1.1.0-20170606.171056-26.pom"],
        ["org.onap.dcaegen2", "/org/onap/dcaegen2/1.2.0-SNAPSHOT/dcaegen2-1.2.0-20180403.182529-10.pom"],
        ["io.fd.vpp", "/io/fd/vpp/jvpp/16.06/jvpp-16.06.jar"],
    ]

    for url in test_url_2_par:
        a = util.create_repo_target_regex(url[0])
        a_regex = re.compile(a)
        assert a_regex.match(url[1]) is not None
