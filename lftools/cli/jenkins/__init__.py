# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Jenkins information."""

__author__ = 'Trevor Bramwell'


import click
import jenkins as jenkins_python  # Don't confuse this with the function ...
from six.moves.urllib.error import HTTPError

from lftools.cli.jenkins.builds import builds
from lftools.cli.jenkins.nodes import nodes
from lftools.cli.jenkins.plugins import plugins_init


@click.group()
@click.option('-s', '--server', type=str, required=True, envvar='JENKINS_URL')
@click.option('-u', '--user', type=str, required=True, envvar='JENKINS_USER')
@click.option('-p', '--password', type=str, required=True,
              envvar='JENKINS_PASSWORD')
@click.pass_context
def jenkins_cli(ctx, server, user, password):
    """Query information about the Jenkins Server."""
    # Initial the Jenkins object and pass it to sub-commands
    ctx.obj['server'] = jenkins_python.Jenkins(
        server,
        username=user,
        password=password)


@click.command()
@click.pass_context
def get_credentials(ctx):
    """Print all available Credentials."""
    server = ctx.obj['server']
    groovy_script = """
import com.cloudbees.plugins.credentials.*

println "Printing all the credentials and passwords..."
def creds = com.cloudbees.plugins.credentials.CredentialsProvider.lookupCredentials(
    com.cloudbees.plugins.credentials.common.StandardUsernameCredentials.class,
    Jenkins.instance,
    null,
    null
);

for (c in creds) {
    try {
        println(c.id + " : " + c.password )
    } catch (MissingPropertyException) {}
}
"""
    result = server.run_script(groovy_script)
    print(result)


@click.command()
@click.argument('groovy_file')
@click.pass_context
def groovy(ctx, groovy_file):
    """Run a groovy script."""
    with open(groovy_file, 'r') as f:
        data = f.read()

    server = ctx.obj['server']
    result = server.run_script(data)
    print(result)


@click.command()
@click.option("-n/-y", is_flag=True, prompt="Quiet down Jenkins?", required=True)
@click.pass_context
def quiet_down(ctx, n):
    """Put Jenkins into 'Quiet Down' mode."""
    version = ctx.obj['server'].get_version()
    # Ask permission first
    if n:
        try:
            ctx.obj['server'].quiet_down()
        except HTTPError as m:
            if m.code == 405:
                print("\n[%s]\nJenkins %s does not support Quiet Down "
                      "without a CSRF Token. (CVE-2017-04-26)\nPlease "
                      "file a bug with 'python-jenkins'" % (m, version))
            else:
                raise m


jenkins_cli.add_command(plugins_init, name='plugins')
jenkins_cli.add_command(nodes)
jenkins_cli.add_command(builds)
jenkins_cli.add_command(get_credentials, name='get-credentials')
jenkins_cli.add_command(groovy)
jenkins_cli.add_command(quiet_down, name='quiet-down')
