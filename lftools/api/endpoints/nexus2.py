# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################

"""Nexus2 REST API interface."""
import json
import logging

from lftools import config
import lftools.api.client as client

log = logging.getLogger(__name__)


class Nexus2(client.RestApi):
    """API endpoint wrapper for Nexus2."""

    def __init__(self, **params):
        """Initialize the class."""
        self.params = params
        self.fqdn = self.params["fqdn"]
        if "creds" not in self.params:
            creds = {
                "authtype": "basic",
                "username": config.get_setting(self.fqdn, "username"),
                "password": config.get_setting(self.fqdn, "password"),
                "endpoint": config.get_setting(self.fqdn, "endpoint"),
            }
            params["creds"] = creds

        super(Nexus2, self).__init__(**params)

    def get_repos(self):
        pass

    def create_repo(self, id, name, provider, policy):
        """Create a new repository.

        :param id: the ID to use
        :param name: the name of the repo
        :param provider: the repo type [Maven1, Maven2, npm, NuGet, Rubygems]
        :param policy: the repo policy [Release,Snapshot]
        """
        pass

    def get_roles(self):
        pass

    def add_roles(self):
        pass

    def get_privileges(self):
        pass

    def add_privilege(self):
        pass

    def list_users(self):
        # http://192.168.1.31:8081/nexus/service/local/plexus_users/allConfigured?_dc=1

        print('hi')

    def add_user(self):
        pass
