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

__author__ = "Trevor Bramwell"


import logging

import click
from six.moves.urllib.error import HTTPError

from lftools.cli.jenkins.builds import builds
from lftools.cli.jenkins.jobs import jobs
from lftools.cli.jenkins.nodes import nodes
from lftools.cli.jenkins.plugins import plugins_init
from lftools.cli.jenkins.token import token
from lftools.jenkins import Jenkins

log = logging.getLogger(__name__)


@click.group()
@click.option("-c", "--conf", type=str, default=None, help="Path to jenkins_jobs.ini config.")
@click.option(
    "-s",
    "--server",
    type=str,
    envvar="JENKINS_URL",
    default="jenkins",
    help="The URL to a Jenkins server. Alternatively the jenkins_jobs.ini "
    "section to parse for url/user/password configuration if available.",
)
@click.option("-u", "--user", type=str, envvar="JENKINS_USER", default="admin")
@click.option("-p", "--password", type=str, envvar="JENKINS_PASSWORD")
@click.pass_context
def jenkins_cli(ctx, server, user, password, conf):
    """Query information about the Jenkins Server."""
    # Initial the Jenkins object and pass it to sub-commands
    ctx.obj["jenkins"] = Jenkins(server, user, password, config_file=conf)


@click.command()
@click.pass_context
def get_credentials(ctx):
    """Print all available Credentials."""
    jenkins = ctx.obj["jenkins"]
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
    result = jenkins.server.run_script(groovy_script)
    log.info(result)


@click.command()
@click.pass_context
def get_secrets(ctx):
    """Print all available secrets."""
    jenkins = ctx.obj["jenkins"]
    groovy_script = """
import com.cloudbees.plugins.credentials.*

println "Printing all secrets..."
def creds = com.cloudbees.plugins.credentials.CredentialsProvider.lookupCredentials(
    com.cloudbees.plugins.credentials.common.StandardCredentials.class,
    Jenkins.instance,
    null,
    null
);

for (c in creds) {
    try {
        println(c.id + " : " + c.secret )
    } catch (MissingPropertyException) {}
}
"""
    result = jenkins.server.run_script(groovy_script)
    log.info(result)


@click.command()
@click.pass_context
def get_private_keys(ctx):
    """Print all available SSH User Private Keys."""
    jenkins = ctx.obj["jenkins"]
    groovy_script = """
import com.cloudbees.plugins.credentials.*
import com.cloudbees.jenkins.plugins.sshcredentials.impl.BasicSSHUserPrivateKey

println "Printing all SSH User Private keys ..."
def creds = com.cloudbees.plugins.credentials.CredentialsProvider.lookupCredentials(
    com.cloudbees.plugins.credentials.Credentials.class,
    Jenkins.instance,
    null,
    null
);

for (c in creds) {
    if(c instanceof BasicSSHUserPrivateKey) {
        println("SSH Private key ID: " + c.getId())
        println("SSH User name: " + c.getUsername())
        println("SSH Private key passphrase: " + c.getPassphrase())
        println("SSH Private key: " + c.getPrivateKey())
    }
}
"""
    result = jenkins.server.run_script(groovy_script)
    log.info(result)


@click.command()
@click.argument("groovy_file")
@click.pass_context
def groovy(ctx, groovy_file):
    """Run a groovy script."""
    with open(groovy_file, "r") as f:
        data = f.read()

    jenkins = ctx.obj["jenkins"]
    result = jenkins.server.run_script(data)
    log.info(result)


@click.command()
@click.option("-n/-y", is_flag=True, prompt="Quiet down Jenkins?", required=True)
@click.pass_context
def quiet_down(ctx, n):
    """Put Jenkins into 'Quiet Down' mode."""
    jenkins = ctx.obj["jenkins"]
    version = jenkins.server.get_version()
    # Ask permission first
    if n:
        try:
            jenkins.server.quiet_down()
        except HTTPError as m:
            if m.code == 405:
                log.error(
                    "\n[%s]\nJenkins %s does not support Quiet Down "
                    "without a CSRF Token. (CVE-2017-04-26)\nPlease "
                    "file a bug with 'python-jenkins'" % (m, version)
                )
            else:
                raise m


@click.command()
@click.option(
    "--force", is_flag=True, default=False, help="Forcibly remove nodes, use only if the non-force version fails."
)
@click.pass_context
def remove_offline_nodes(ctx, force):
    """Remove any offline nodes."""
    jenkins = ctx.obj["jenkins"]
    groovy_script = """
import hudson.model.*

def numberOfflineNodes = 0
def numberNodes = 0

slaveNodes = hudson.model.Hudson.instance

for (slave in slaveNodes.nodes) {
    def node = slave.computer
    numberNodes ++
    println ""
    println "Checking node ${node.name}:"
    println '\tcomputer.isOffline: ${slave.getComputer().isOffline()}'
    println '\tcomputer.offline: ${node.offline}'

    if (node.offline) {
        numberOfflineNodes ++
        println '\tRemoving node ${node.name}'
        slaveNodes.removeNode(slave)
    }
}

println "Number of Offline Nodes: " + numberOfflineNodes
println "Number of Nodes: " + numberNodes
"""

    force_script = """
import jenkins.*
import jenkins.model.*
import hudson.*
import hudson.model.*

for (node in Jenkins.instance.computers) {
    try {
        println "Checking node: ${node.name}"
        println "\tdisplay-name: ${node.properties.displayName}"
        println "\toffline: ${node.properties.offline}"
        println "\ttemporarily-offline: ${node.properties.temporarilyOffline}"
        if (node.properties.offline) {
            println "Removing bad node: ${node.name}"
            Jenkins.instance.removeComputer(node)
        }
        println ""
    }
    catch (NullPointerException nullPointer) {
        println "NullPointerException caught"
        println ""
    }
}
"""

    if force:
        result = jenkins.server.run_script(force_script)
    else:
        result = jenkins.server.run_script(groovy_script)
    log.info(result)


jenkins_cli.add_command(plugins_init, name="plugins")
jenkins_cli.add_command(nodes)
jenkins_cli.add_command(builds)
jenkins_cli.add_command(get_credentials, name="get-credentials")
jenkins_cli.add_command(get_secrets, name="get-secrets")
jenkins_cli.add_command(get_private_keys, name="get-private-keys")
jenkins_cli.add_command(groovy)
jenkins_cli.add_command(jobs)
jenkins_cli.add_command(quiet_down, name="quiet-down")
jenkins_cli.add_command(remove_offline_nodes, name="remove-offline-nodes")
jenkins_cli.add_command(token)
