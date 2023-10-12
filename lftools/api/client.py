# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019, 2023 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""REST API interface using Requests."""
from __future__ import annotations

import json
from typing import Any, Dict, Optional, Tuple

import requests


class RestApi(object):
    """A generic REST API interface."""

    def __init__(self, **kwargs: Dict[str, str]) -> None:
        """Initialize the REST API class."""
        self.params: Dict[str, Dict[str, str]] = kwargs

        if kwargs["creds"]:
            self.creds: Dict[str, str] = kwargs["creds"]

        if "timeout" not in self.params:
            self.timeout: Optional[int] = None

        self.endpoint: str = self.creds["endpoint"]

        if self.creds["authtype"] == "basic":
            self.username: str = self.creds["username"]
            self.password: str = self.creds["password"]
            self.r: requests.Session = requests.Session()
            self.r.auth = (self.username, self.password)
            self.r.headers.update({"Content-Type": "application/json; charset=UTF-8", "Accept": "application/json"})

        if self.creds["authtype"] == "token":
            self.token: str = self.creds["token"]
            self.r = requests.Session()
            self.r.headers.update({"Authorization": f"Token {self.token}"})
            self.r.headers.update({"Content-Type": "application/json"})

    def _request(
        self, url: str, method: str, data: Optional[Any] = None, timeout: int = 30
    ) -> requests.Response | Tuple[requests.Response, Optional[Dict[str, Any] | str]]:
        """Execute the request."""
        resp: requests.Response = self.r.request(method, self.endpoint + url, data=data, timeout=timeout)

        # Some massaging to make our gerrit python code work
        if resp.status_code == 409:
            return resp

        if resp.text:
            try:
                if "application/json" in resp.headers["Content-Type"]:
                    remove_xssi_magic: str = resp.text.replace(")]}'", "")
                    body: Optional[Dict[str, Any] | str] = json.loads(remove_xssi_magic)
                else:
                    body = resp.text
            except ValueError:
                body = None
        else:
            body = None
            return resp

        return resp, body

    def get(self, url: str, **kwargs) -> requests.Response | Tuple[requests.Response, Optional[Dict[str, Any] | str]]:
        """HTTP GET request."""
        return self._request(url, "GET", **kwargs)

    def patch(self, url: str, **kwargs) -> requests.Response | Tuple[requests.Response, Optional[Dict[str, Any] | str]]:
        """HTTP PATCH request."""
        return self._request(url, "PATCH", **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response | Tuple[requests.Response, Optional[Dict[str, Any] | str]]:
        """HTTP POST request."""
        return self._request(url, "POST", **kwargs)

    def put(self, url: str, **kwargs) -> requests.Response | Tuple[requests.Response, Optional[Dict[str, Any] | str]]:
        """HTTP PUT request."""
        return self._request(url, "PUT", **kwargs)

    def delete(
        self, url: str, **kwargs
    ) -> requests.Response | Tuple[requests.Response, Optional[Dict[str, Any] | str]]:
        """HTTP DELETE request."""
        return self._request(url, "DELETE", **kwargs)
