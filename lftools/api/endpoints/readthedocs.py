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
import lftools.api.client as client


class ReadTheDocs(client.RestApi):
    """
    API endpoint wrapper for readthedocs.org
    Be sure to always include the trailing / when adding
    new methods.
    """

    def __init__(self, **params):
        params['token'] = config.get_setting('rtd', 'token')
        params['endpoint'] = config.get_setting('rtd', 'endpoint')
        super(ReadTheDocs, self).__init__(**params)

    def project_list(self, **kwargs):
        """
        This returns the list of projects by their slug name ['slug'],
        not their pretty name ['name']. Since we use these for getting
        details, triggering builds, etc., the pretty name is useless.
        :param kwargs:
        :return: [projects]
        """

        data = json.loads(self.get('projects/')[1])
        project_data = data['results']
        project_list = []

        for project in project_data:
            project_list.append(project['slug'])

        return project_list

    def project_details(self, project, **kwargs):
        """
        Retrieves the details of a specific project
        :param project: The project's slug
        :param kwargs:
        :return: {result}
        """

        result = self.clean_json_response(self.get('projects/{}/'.format(project), **kwargs))  # NOQA
        return result

    def project_version_list(self, project):
        """
        Retrieve a list of all versions of a project

        :param project: The project's slug
        :return: {result}
        """

        result = self.clean_json_response(self.get('projects/{}/versions/'.format(project)))  # NOQA
        return result

    def project_version_details(self, project, version):
        """
        Retrieve details of a single version.

        :param project: The project's slug
        :param version: The version's slug
        :return: {result}
        """

        result = self.clean_json_response(self.get('projects/{}/versions/{}/'.format(project, version)))  # NOQA
        return result

    # This is implemented per their docs, however they do not appear to have
    # it working yet as this always returns a 404
    def project_version_update(self, project, version, active,
                               privacy_level):
        """
        Edit a version.

        :param project: The project slug
        :param version: The version slug
        :param active: 'true' or 'false'
        :param privacy_level: 'public' or 'private'
        :return: {result}
        """

        data = {
            'active': active,
            'privacy_level': privacy_level
        }

        json_data = json.dumps(data)
        result = self.patch('projects/{}/version/{}/'.format(project, version),
                            data=json_data)
        return result

    def project_create(self, name, repository_url, repository_type, homepage,
                       programming_language, language, **kwargs):
        """
        Create a new Read the Docs project

        :param name: Project name. Any spaces will convert to dashes for the
                        project slug
        :param repository_url:
        :param repository_type: Valid types are git, hg, bzr, and svn
        :param homepage:
        :param programming_language: valid programming language abbreviations
                        are py, java, js, cpp, ruby, php, perl, go, c, csharp,
                        swift, vb, r, objc, css, ts, scala, groovy, coffee,
                        lua, haskell, other, words
        :param language: Most two letter language abbreviations: en, es, etc.
        :param kwargs:
        :return: {results}
        """

        data = {
            'name': name,
            'repository': {
                'url': repository_url,
                'type': repository_type
            },
            'homepage': homepage,
            'programming_language': programming_language,
            'language': language
        }

        json_data = json.dumps(data)
        result = self.clean_json_response(self.post('projects/', data=json_data, **kwargs))  # NOQA
        return result

    def project_build_list(self, project, **kwargs):
        """
        Retrieves the project's build list

        :param project: The project's slug
        :param kwargs:
        :return: {result}
        """

        result = self.clean_json_response(self.get('projects/{}/builds/'.format(project), **kwargs))  # NOQA
        return result

    def project_build_details(self, project, build_id, **kwargs):
        """
        Retrieves the details of a specific build

        :param project: The project's slug
        :param build_id: The build id
        :param kwargs:
        :return: {result}
        """

        result = self.clean_json_response(self.get('projects/{}/builds/{}/'.format(project, build_id)))  # NOQA
        return result

    def project_build_trigger(self, project, version):
        """
        Triggers a project build

        :param project: The project's slug
        :param version: The version of the project to build
                        (must be an active version)
        :return: {result}
        """

        result = self.clean_json_response(self.post('projects/{}/versions/{}/builds/'.format(project, version)))  # NOQA
        return result
