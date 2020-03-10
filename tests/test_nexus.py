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

from lftools.nexus import cmd
from lftools.nexus import util


FIXTURE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures")


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


def test_create_repo_target_regex():
    """Test create_repo_target_regex() command."""

    odlparent = util.create_repo_target_regex("org.opendaylight.odlparent")
    odlparent_regex = re.compile(odlparent)
    assert odlparent_regex.match(
        "/org/opendaylight/odlparent/odlparent" "/4.0.0-SNAPSHOT/odlparent-4.0.0-20180424.132124-69.pom"
    )

    honeycomb = util.create_repo_target_regex("org.opendaylight.honeycomb.vbd")
    honeycomb_regex = re.compile(honeycomb)
    assert honeycomb_regex.match(
        "/org/opendaylight/honeycomb/vbd/odl-vbd" "/1.4.0-SNAPSHOT/odl-vbd-1.4.0-20180422.024456-12-features.xml"
    )

    mso = util.create_repo_target_regex("org.openecomp.mso")
    mso_regex = re.compile(mso)
    assert mso_regex.match("/org/openecomp/mso/" "1.1.0-SNAPSHOT/mso-1.1.0-20170606.171056-26.pom")

    dcaegen2 = util.create_repo_target_regex("org.onap.dcaegen2")
    dcaegen2_regex = re.compile(dcaegen2)
    assert dcaegen2_regex.match("/org/onap/dcaegen2/" "1.2.0-SNAPSHOT/dcaegen2-1.2.0-20180403.182529-10.pom")

    vpp = util.create_repo_target_regex("io.fd.vpp")
    vpp_regex = re.compile(vpp)
    assert vpp_regex.match("/io/fd/vpp/jvpp/16.06/jvpp-16.06.jar")
