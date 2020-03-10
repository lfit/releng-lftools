# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""REST API interface using Requests."""

import json

import requests


class RestApi(object):
    """A generic REST API interface."""

    def __init__(self, **params):
        """Initialize the REST API class."""
        self.params = params

        if params["creds"]:
            self.creds = params["creds"]

        if "timeout" not in self.params:
            self.timeout = None

        self.endpoint = self.creds["endpoint"]

        if self.creds["authtype"] == "basic":
            self.username = self.creds["username"]
            self.password = self.creds["password"]
            self.r = requests.Session()
            self.r.auth = (self.username, self.password)
            self.r.headers.update({"Content-Type": "application/json; charset=UTF-8", "Accept": "application/json"})

        if self.creds["authtype"] == "token":
            self.token = self.creds["token"]
            self.r = requests.Session()
            self.r.headers.update({"Authorization": "Token {}".format(self.token)})
            self.r.headers.update({"Content-Type": "application/json"})

    def _request(self, url, method, data=None, timeout=30):
        """Execute the request."""
        resp = self.r.request(method, self.endpoint + url, data=data, timeout=timeout)

        # Some massaging to make our gerrit python code work
        if resp.status_code == 409:
            return resp

        if resp.text:
            try:
                if "application/json" in resp.headers["Content-Type"]:
                    remove_xssi_magic = resp.text.replace(")]}'", "")
                    body = json.loads(remove_xssi_magic)
                else:
                    body = resp.text
            except ValueError:
                body = None
        else:
            body = None
            return resp

        return resp, body

    def get(self, url, **kwargs):
        """HTTP GET request."""
        return self._request(url, "GET", **kwargs)

    def patch(self, url, **kwargs):
        """HTTP PATCH request."""
        return self._request(url, "PATCH", **kwargs)

    def post(self, url, **kwargs):
        """HTTP POST request."""
        return self._request(url, "POST", **kwargs)

    def put(self, url, **kwargs):
        """HTTP PUT request."""
        return self._request(url, "PUT", **kwargs)

    def delete(self, url, **kwargs):
        """HTTP DELETE request."""
        return self._request(url, "DELETE", **kwargs)
