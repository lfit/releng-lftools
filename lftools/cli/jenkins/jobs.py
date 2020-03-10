# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2018 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Jenkins Jobs."""

__author__ = "Anil Belur"

import click

enable_disable_jobs = """
import jenkins.*
import jenkins.model.*
import hudson.*
import hudson.model.*

def jobTypes = [hudson.model.FreeStyleProject.class]

def filter = {{job->
    if (job.disabled == true) {{
        println("${{job.fullName}}")
    }}
    job.getDisplayName().contains("{0}")
}}

def disableClosure = {{job->job.{1}()}}

jobTypes.each{{ className->
    jenkins.model.Jenkins.instance.getAllItems(className).findAll(filter).each(disableClosure)}}
"""


@click.group()
@click.pass_context
def jobs(ctx):
    """Command to update Jenkins Jobs."""
    pass


@click.command()
@click.argument("regex")
@click.pass_context
def enable(ctx, regex):
    """Enable all Jenkins jobs matching REGEX."""
    jenkins = ctx.obj["jenkins"]

    result = jenkins.server.run_script(enable_disable_jobs.format(regex, "enable"))
    print(result)


@click.command()
@click.argument("regex")
@click.pass_context
def disable(ctx, regex):
    """Disable all Jenkins jobs matching REGEX."""
    jenkins = ctx.obj["jenkins"]

    result = jenkins.server.run_script(enable_disable_jobs.format(regex, "disable"))
    print(result)


jobs.add_command(enable)
jobs.add_command(disable)
