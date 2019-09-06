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
        self.endpoint = self.params['endpoint']
        self.token = self.params['token']

        if 'timeout' not in self.params:
            self.timeout = None

        self.r = requests.Session()
        self.r.headers.update({'Authorization': 'Token {}'.format(self.token)})
        self.r.headers.update({'Content-Type': 'application/json'})

    def _request(self, url, method, data=None, timeout=10):
        """Execute the requested request."""
        resp = self.r.request(method, self.endpoint + url, data=data,
                              timeout=timeout)

        if resp.text:
            try:
                if resp.headers['Content-Type'] == 'application/json':
                    body = json.loads(resp.text)
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
        return self._request(url, 'GET', **kwargs)

    def patch(self, url, **kwargs):
        """HTTP PATCH request."""
        return self._request(url, 'PATCH', **kwargs)

    def post(self, url, **kwargs):
        """HTTP POST request."""
        return self._request(url, 'POST', **kwargs)

    def put(self, url, **kwargs):
        """HTTP PUT request."""
        return self._request(url, 'PUT', **kwargs)

    def delete(self, url, **kwargs):
        """HTTP DELETE request."""
        return self._request(url, 'DELETE', **kwargs)
