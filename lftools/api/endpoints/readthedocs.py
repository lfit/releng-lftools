# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################

"""Read the Docs REST API interface."""

import json

from lftools import config
import lftools.api.client as client


class ReadTheDocs(client.RestApi):
    """API endpoint wrapper for readthedocs.org.

    Be sure to always include the trailing "/" when adding
    new methods.
    """

    def __init__(self, **params):
        """Initialize the class."""
        if 'token' not in params:
            params['token'] = config.get_setting('rtd', 'token')
        if 'endpoint' not in params:
            params['endpoint'] = config.get_setting('rtd', 'endpoint')
        super(ReadTheDocs, self).__init__(**params)

    def project_list(self):
        """Return a list of projects.

        This returns the list of projects by their slug name ['slug'],
        not their pretty name ['name']. Since we use these for getting
        details, triggering builds, etc., the pretty name is useless.

        :param kwargs:
        :return: [projects]
        """
        result = self.get('projects/')[1]  # NOQA
        more_results = None
        data = result['results']
        project_list = []

        if result['next']:
            more_results = result['next'].rsplit('/', 1)[-1]

        if more_results:
            while more_results is not None:
                get_more_results = self.get('projects/' + more_results)[1]
                data.append(get_more_results['results'])
                more_results = get_more_results['next']

                if more_results is not None:
                    more_results = more_results.rsplit('/', 1)[-1]

        for project in data:
            project_list.append(project['slug'])

        return project_list

    def project_details(self, project):
        """Retrieve the details of a specific project.

        :param project: The project's slug
        :param kwargs:
        :return: {result}
        """
        result = self.get('projects/{}/'.format(project))[1]
        return result

    def project_version_list(self, project):
        """Retrieve a list of all ACTIVE versions of a project.

        :param project: The project's slug
        :return: {result}
        """
        result = self.get('projects/{}/versions/?active=True'
                          .format(project))[1]
        more_results = None
        versions = []

        # I feel like there must be a better way...but, this works. -DWTalton
        initial_versions = result['results']
        for version in initial_versions:
            versions.append(version['slug'])

        if result['next']:
            more_results = result['next'].rsplit('/', 1)[-1]

        if more_results:
            while more_results is not None:
                get_more_results = self.get('projects/{}/versions/'
                                            .format(project) + more_results)[1]
                more_results = get_more_results['next']

                for version in get_more_results['results']:
                    versions.append(version['slug'])

                if more_results is not None:
                    more_results = more_results.rsplit('/', 1)[-1]

        return versions

    def project_version_details(self, project, version):
        """Retrieve details of a single version.

        :param project: The project's slug
        :param version: The version's slug
        :return: {result}
        """
        result = self.get('projects/{}/versions/{}/'
                          .format(project, version))[1]
        return result

    # This is implemented per their docs, however they do not appear to have
    # it working yet as this always returns a 404
    def project_version_update(self, project, version, active,
                               privacy_level):
        """Edit a version.

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
        """Create a new Read the Docs project.

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
        result = self.post('projects/', data=json_data, **kwargs)
        return result

    def project_build_list(self, project, **kwargs):
        """Retrieve the project's running build list.

        For future expansion, the statuses are cloning,
        installing, building.

        :param project: The project's slug
        :param kwargs:
        :return: {result}
        """
        result = self.get('projects/{}/builds/?running=True'
                          .format(project), **kwargs)[1]

        if result['count'] > 0:
            return result
        else:
            return "There are no active builds."

    def project_build_details(self, project, build_id, **kwargs):
        """Retrieve the details of a specific build.

        :param project: The project's slug
        :param build_id: The build id
        :param kwargs:
        :return: {result}
        """
        result = self.get('projects/{}/builds/{}/'
                          .format(project, build_id))[1]
        return result

    def project_build_trigger(self, project, version):
        """Trigger a project build.

        :param project: The project's slug
        :param version: The version of the project to build
                        (must be an active version)
        :return: {result}
        """
        result = self.post('projects/{}/versions/{}/builds/'
                           .format(project, version))[1]
        return result
