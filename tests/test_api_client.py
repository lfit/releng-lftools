# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2018 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Test generic REST client."""

import responses

import lftools.api.client as client

creds = {"authtype": "token", "endpoint": "", "token": "xyz"}
c = client.RestApi(creds=creds)


@responses.activate
def test_get():
    responses.add(responses.GET, "https://fakeurl/", json={"success": "get"}, status=200, match_querystring=True)
    resp = c.get("https://fakeurl/")
    assert resp[1] == {"success": "get"}


@responses.activate
def test_patch():
    responses.add(
        responses.PATCH, url="https://fakeurl/", json={"success": "patch"}, status=204, match_querystring=True
    )
    resp = c.patch("https://fakeurl/")
    assert resp[1] == {"success": "patch"}


@responses.activate
def test_post():
    responses.add(responses.POST, "https://fakeurl/", json={"success": "post"}, status=201, match_querystring=True)
    resp = c.post("https://fakeurl/")
    assert resp[1] == {"success": "post"}


@responses.activate
def test_put():
    responses.add(responses.PUT, "https://fakeurl/", json={"success": "put"}, status=200, match_querystring=True)
    resp = c.put("https://fakeurl/")
    assert resp[1] == {"success": "put"}


@responses.activate
def test_delete():
    responses.add(responses.DELETE, "https://fakeurl/", json={"success": "delete"}, status=200, match_querystring=True)
    resp = c.delete("https://fakeurl/")
    assert resp[1] == {"success": "delete"}
