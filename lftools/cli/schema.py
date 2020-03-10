# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Verify YAML Schema."""

from __future__ import print_function

import click

from lftools.schema import check_schema_file


@click.group()
@click.pass_context
def schema(ctx):
    """Verify YAML Schema."""
    pass


@click.command(name="verify")
@click.argument("yamlfile")
@click.argument("schemafile")
@click.pass_context
def verify_schema(ctx, yamlfile, schemafile):
    """Verify YAML Schema.

    YAMLFILE: Release YAML file to be validated.

    SCHEMAFILE: SCHEMA file to validate against.
    """
    check_schema_file(yamlfile, schemafile)


schema.add_command(verify_schema)
