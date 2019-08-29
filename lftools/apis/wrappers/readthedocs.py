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
import json

from lftools import config
import lftools.apis.client as client
import lftools.apis.exceptions as exceptions


class ReadTheDocs(client.RestApi):

    def __init__(self, **params):
        params['token'] = config.get_setting('rtd', 'token')
        params['endpoint'] = config.get_setting('rtd', 'endpoint')
        super(ReadTheDocs, self).__init__(**params)

    def project_list(self, **kwargs):
        return self.get('projects/')

    def project_details(self, project=None, **kwargs):
        if slug is not None:
            return self.get('projects/{}/'.format(project), **kwargs)
        else:
            return "Please pass the project name, e.g. project_details(project='foo')"

    def project_create(self, **kwargs):
        return self.post('projects', **kwargs)

    def build_list(self, project=None, **kwargs):
        if project is not None:
            return self.get('projects/{}/builds/', **kwargs)
        else:
            return "Please pass the project name, e.g. project_details(project='foo')"

    def build_details(self, project=None, build_id=None, **kwargs):
        if project is not None:
            if build_id is not None:
                return self.get('projects/{}/builds/{}/'.format(project, build_id))
            else:
                return "You must include the build number, e.g. build_id=123"
        else:
            return "You must include the project name and build number e.g project=myproject build_id=<int>"

# # dict
# payload = {
#   "name": "someproject",
#   "repository": {
#       "url": "https://github.com/lfit-sandbox/test",
#       "type": "git"
#   },
#   "homepage": "http://lfit-sandbox-test.readthedocs.io/",
#   "programming_language": "py",
#   "language": "en"
# }
#
# brap = json.dumps(payload)
#
# foo = ReadTheDocs()
# print(foo.build_details(build_id=123))

