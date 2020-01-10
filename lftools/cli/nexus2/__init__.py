# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2019 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################

"""Nexus2 REST API sub-interfaces."""

__author__ = 'DW Talton'


from .privilege import *
from .repository import *
from .role import *
from .user import *
from lftools.api.endpoints import nexus2


@click.group(name="nexus2")
@click.option('-c', '--config-entry', 'fqdn')
@click.pass_context
def nexus_two(ctx, fqdn):
    # """Provide an interface to Nexus2."""
    nexus2_obj = nexus2.Nexus2(fqdn=fqdn)
    ctx.obj = {"nexus2": nexus2_obj}
    pass


nexus_two.add_command(privilege)
nexus_two.add_command(repo)
nexus_two.add_command(role)
nexus_two.add_command(user)