# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################

"""Nexus3 REST API sub-interfaces."""

from .asset import *
from .privilege import *
from .repository import *
from .role import *
from .script import *
from .tag import *
from .task import *
from .user import *


@click.group()
@click.argument("fqdn")
@click.pass_context
def nexus3(ctx, fqdn):
    """Provide an interface to Nexus3."""
    nexus_obj = nexus.Nexus(fqdn=fqdn)
    ctx.obj = {"nexus": nexus_obj}
    pass


nexus3.add_command(asset)
nexus3.add_command(privilege)
nexus3.add_command(repository)
nexus3.add_command(role)
nexus3.add_command(script)
nexus3.add_command(tag)
nexus3.add_command(task)
nexus3.add_command(user)
