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

import re
import requests

import pytest

from lftools.nexus import cmd
from lftools.nexus import util


def test_create_repo_target_regex():
    """Test create_repo_target_regex() command."""

    odlparent = util.create_repo_target_regex('org.opendaylight.odlparent')
    odlparent_regex = re.compile(odlparent)
    assert odlparent_regex.match(
        '/org/opendaylight/odlparent/odlparent'
        '/4.0.0-SNAPSHOT/odlparent-4.0.0-20180424.132124-69.pom'
    )

    honeycomb = util.create_repo_target_regex('org.opendaylight.honeycomb.vbd')
    honeycomb_regex = re.compile(honeycomb)
    assert honeycomb_regex.match(
        '/org/opendaylight/honeycomb/vbd/odl-vbd'
        '/1.4.0-SNAPSHOT/odl-vbd-1.4.0-20180422.024456-12-features.xml'
    )

    mso = util.create_repo_target_regex('org.openecomp.mso')
    mso_regex = re.compile(mso)
    assert mso_regex.match(
        '/org/openecomp/mso/'
        '1.1.0-SNAPSHOT/mso-1.1.0-20170606.171056-26.pom'
    )

    dcaegen2 = util.create_repo_target_regex('org.onap.dcaegen2')
    dcaegen2_regex = re.compile(dcaegen2)
    assert dcaegen2_regex.match(
        '/org/onap/dcaegen2/'
        '1.2.0-SNAPSHOT/dcaegen2-1.2.0-20180403.182529-10.pom'
    )

    vpp = util.create_repo_target_regex('io.fd.vpp')
    vpp_regex = re.compile(vpp)
    assert vpp_regex.match('/io/fd/vpp/jvpp/16.06/jvpp-16.06.jar')


def test_release_staging_repos(responses):
    """Test release_staging_repos() command."""
    good_url = "https://nexus.example.org"
    # Prepare response for Nexus initialization
    responses.add(responses.GET,
                  "{}/service/local/repo_targets".format(good_url),
                  json=None, status=200)
    # The responses provide implicit assertions.
    responses.add(responses.POST, "{}/service/local/staging/bulk/promote".format(good_url),
                  json=None, status=201)
    responses.add(responses.POST, "{}/service/local/staging/bulk/drop".format(good_url),
                  json=None, status=201)

    # Test successful single release.
    cmd.release_staging_repos(("release-1",), good_url)

    # Test successful multiple release.
    cmd.release_staging_repos(("release-1", "release-2", "release-3"),
                              good_url)

    # Test promote failure
    bad_url1 = "https://nexus-fail1.example.org"
    responses.add(responses.GET,
                  "{}/service/local/repo_targets".format(bad_url1),
                  json=None, status=200)
    responses.add(responses.POST,
                  "{}/service/local/staging/bulk/promote".format(bad_url1),
                  status=401)
    with pytest.raises(requests.HTTPError):
        cmd.release_staging_repos(("release-1",), bad_url1)

    # Test drop failure
    bad_url2 = "https://nexus-fail2.example.org"
    responses.add(responses.GET,
                  "{}/service/local/repo_targets".format(bad_url2),
                  json=None, status=200)
    responses.add(responses.POST,
                  "{}/service/local/staging/bulk/promote".format(bad_url2),
                  status=201)
    responses.add(responses.POST,
                  "{}/service/local/staging/bulk/drop".format(bad_url2),
                  status=403)
    with pytest.raises(requests.HTTPError):
        cmd.release_staging_repos(("release-1",), bad_url2)
