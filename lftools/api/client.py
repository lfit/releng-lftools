# -*- coding: utf-8 -*-
# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################


# A REST API interface using Requests.

import json

import requests


class RestApi(object):

    def __init__(self, **params):
        self.params = params
        self.endpoint = self.params['endpoint']
        self.token = self.params['token']

        if 'timeout' not in self.params:
            self.timeout = None

        self.r = requests.Session()
        self.r.headers.update({'Authorization': 'Token {}'.format(self.token)})
        self.r.headers.update({'Content-Type': 'application/json'})

    def _request(self, url, method, data=None, timeout=5):
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
        return self._request(url, 'GET', **kwargs)

    def patch(self, url, **kwargs):
        return self._request(url, 'PATCH', **kwargs)

    def post(self, url, **kwargs):
        return self._request(url, 'POST', **kwargs)

    def put(self, url, **kwargs):
        return self._request(url, 'PUT', **kwargs)

    def delete(self, url, **kwargs):
        return self._request(url, 'DELETE', **kwargs)

    def clean_json_response(self, data, **kwargs):
        clean_data = json.loads(data[1])
        return clean_data
