# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################

"""Gerrit REST API interface."""

import json

from lftools import config
import lftools.api.client as client


class Gerrit(client.RestApi):
    """API endpoint wrapper for Gerrit.

    Be sure to always include the trailing "/" when adding
    new methods.
    """

    def __init__(self, **params):
        """Initialize the class."""
        self.params = params
        self.fqdn = self.params['fqdn']
        if 'creds' not in self.params:
            creds = {
                'authtype': 'basic',
                'username': config.get_setting(self.fqdn, 'username'),
                'password': config.get_setting(self.fqdn, 'password'),
                'endpoint': config.get_setting(self.fqdn, 'endpoint')
            }
            params['creds'] = creds

        super(Gerrit, self).__init__(**params)

    def add_info_file(self, fqdn, gerrit_project, info_file, **kwargs):
        """Add an INFO file for review to a Project.

        Requires gerrit directory.

        Example:

        gerrit_url gerrit.o-ran-sc.org/r
        gerrit_project test/test1
        """
        # Setup
        # headers = {'Content-Type': 'application/json; charset=UTF-8'}

        ###############################################################
        # INFO.yaml
        # 'POST /changes/'

        # Need exceptions here. we should pass the ISSUE-ID like the signed off by line
        signed_off_by = config.get_setting(fqdn, 'sob')

        if fqdn == 'gerrit.onap.org':
            data = {
                'project': '{}'.format(gerrit_project),
                'subject': 'Automation adds Gitreview\n\nIssue-ID: CIMAN-33\n\nSigned-off-by: {}'.format(signed_off_by),
                'branch': 'master',
            }
        else:
            data = {
                'project': gerrit_project,
                'subject': 'My log message \n\nSigned-off-by: {}'.format(signed_off_by),
                'branch': 'master',
            }

        json_data = json.dumps(data)
        result = self.post('changes/', data=json_data)[1]

        # print(result)
        # print(result['id'])
        # changeid = (result['id'])
        # # 'PUT /changes/{change-id}/edit/path%2fto%2ffile
        # my_info_file = open(info_file)
        # my_info_file_size = os.stat(info_file)
        # headers = {'Content-Type': 'text/plain',
        #            'Content-length': '{}'.format(my_info_file_size)}
        # access_str = 'changes/{}/edit/INFO.yaml'.format(changeid)
        # payload = my_info_file
        # time.sleep(2)
        # result = rest.put(access_str, headers=headers, data=payload)
        # print(result)
        # # 'POST /changes/{change-id}/edit:publish
        # access_str = 'changes/{}/edit:publish'.format(changeid)
        # headers = {'Content-Type': 'application/json; charset=UTF-8'}
        # payload = json.dumps({
        #     "notify": "NONE",
        # })
        # time.sleep(2)
        # result = rest.post(access_str, headers=headers, data=payload)
        # print(result)
        # return (result)
        # ##############################################################
