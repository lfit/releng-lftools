# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2018 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Test deploy command."""

import os

import pytest
import lftools.nexus.cmd as test_cmd


FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "fixtures",
)

@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "nexus"),
)
class TestReleaseStagingRepos():

    def mocked_get_credentials(self, nothing, url):
        """Mocking Get Credentials."""
        return {"nexus": url, "user": "nexus", "password": "nexus"}

    def test_releasestagin_notallowedupdate(self, datafiles, responses, mocker):
        nexus_url = "http://my.gerrit.org/"
        nexus_url_check = "http://my.gerrit.org/service/local/repo_targets"
        mocker.patch("lftools.nexus.cmd.get_credentials", side_effect=self.mocked_get_credentials)
        repo = "autorelease-348900"
        mock_url = "{}service/local/staging/repository/{}/activity".format(nexus_url, repo)
     
        release_staging_xml_result = os.path.join(str(datafiles), "ReleaseStaging-NotAllowUpdatingArtifact.xml")
    
        with open (release_staging_xml_result, 'r') as file:
          nexus_answer = file.read()

        responses.add(responses.GET, mock_url, body=nexus_answer, status=200)
        responses.add(responses.GET, nexus_url_check, body=nexus_answer, status=200)

        with pytest.raises(SystemExit) as cm:
            test_cmd.release_staging_repos([repo], True, nexus_url)

        assert cm.type == SystemExit
        assert cm.value.code == 1

