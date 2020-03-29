# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2020 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################

"""lftools utils command."""

import click
import logging

from lftools import helpers

log = logging.getLogger(__name__)


@click.group()
@click.pass_context
def utils(ctx):
    """Tools to make life easier."""
    pass


@click.command(name="passgen")
@click.argument("length", required=False)
@click.pass_context
def password_generator(ctx, length):
    """Generate a complex password.

    Length defaults to 12 characters if not specified.
    """
    if length:
        length = int(length)
    else:
        length = 12
    log.info(helpers.generate_password(length))


utils.add_command(password_generator)
