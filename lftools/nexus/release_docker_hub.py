# -*- coding: utf-8 -*-
# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2018 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Set of functions to facilitate copying nexus3 release images to docker hub.

Workflow if you do it manually

    sudo docker login       ---> DOCKER Credentials
    sudo docker login nexus3.onap.org:10002 -u <yourLFID>

    TAB1 https://nexus3.onap.org/#browse/search=repository_name%3Ddocker.release
    TAB2 https://hub.docker.com/r/onap

    docker pull nexus3.onap.org:10002/onap/aaf/aaf_hello:2.1.3
    docker images --> imageid --> 991170554e6e
    docker tag 991170554e6e onap/aaf-aaf_hello:2.1.3
    docker push onap/aaf-aaf_hello:2.1.3
    docker image rm --force 991170554e6e

Filter
Find all projects that starts with org and contains repo (if specified).

Set the repo to "" to find all projects that starts with org

Set the repo to a str to find all projects that contains that string
  and starts with org
    repo = "aaf_co"   # onap/aaf/aaf_config,onap/aaf/aaf_core
    repo = "aaf_cm"   # onap/aaf/aaf_cm
    repo = "aa"
    repo = ""         # Find all projects

lftools nexus docker releasedockerhub
"""
from __future__ import print_function

import logging
import socket

import requests
import urllib3

log = logging.getLogger(__name__)

NexusCatalog = []
projects = []
TotTagsToBeCopied = 0

NEXUS3_BASE = ""
NEXUS3_CATALOG = ""
NEXUS3_PROJ_NAME_HEADER = ""
DOCKER_PROJ_NAME_HEADER = ""


def _remove_http_from_url(url):
    """Remove http[s]:// from url."""
    if url.startswith('https://'):
        return url[len('https://'):]
    if url.startswith('http://'):
        return url[len('http://'):]
    return url


def _format_image_id(id):
    """Remove sha256: from beginning of string."""
    if id.startswith("sha256:"):
        return id[len('sha256:'):]
    else:
        return id


def _request_get(url):
    """Execute a request get, return the resp."""
    resp = {}
    try:
        resp = requests.get(url)
    except requests.exceptions.RequestException as excinfo:
        log.debug("in _request_get RequestException. {}".format(type(excinfo)))
        raise requests.HTTPError("Issues with URL: {} - {}".format(url, type(excinfo)))
    except socket.gaierror as excinfo:
        log.debug("in _request_get gaierror. {}".format(type(excinfo)))
        raise requests.HTTPError("Issues with URL: {} - {}".format(url, type(excinfo)))
    except requests.exceptions.ConnectionError as excinfo:
        log.debug("in _request_get ConnectionError. {}".format(type(excinfo)))
        raise requests.HTTPError("Issues with URL: {} - {}".format(url, type(excinfo)))
    except urllib3.exceptions.NewConnectionError as excinfo:
        log.debug("in _request_get NewConnectionError. {}".format(type(excinfo)))
        raise requests.HTTPError("Issues with URL: {} - {}".format(url, type(excinfo)))
    except urllib3.exceptions.MaxRetryError as excinfo:
        log.debug("in _request_get MaxRetryError. {}".format(type(excinfo)))
        raise requests.HTTPError("Issues with URL: {} - {}".format(url, type(excinfo)))
    return resp


def initialize(org_name):
    """Set constant strings."""
    global NEXUS3_BASE
    global NEXUS3_CATALOG
    global NEXUS3_PROJ_NAME_HEADER
    global DOCKER_PROJ_NAME_HEADER
    NEXUS3_BASE = "https://nexus3.{}.org:10002".format(org_name)
    NEXUS3_CATALOG = NEXUS3_BASE + "/v2/_catalog"
    NEXUS3_PROJ_NAME_HEADER = "Nexus3 Project Name"
    DOCKER_PROJ_NAME_HEADER = "Docker HUB Project Name"
