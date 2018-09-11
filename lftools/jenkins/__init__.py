# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2018 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Jenkins."""

__author__ = 'Thanh Ha'

import logging
import os

log = logging.getLogger(__name__)


def jjb_ini():
    """Return jenkins_jobs.ini file location if it exists, None otherwise."""
    global_conf = '/etc/jenkins_jobs/jenkins_jobs.ini'
    user_conf = os.path.join(
        os.path.expanduser('~'),
        '.config',
        'jenkins_jobs',
        'jenkins_jobs.ini')
    local_conf = os.path.join(
        os.getcwd(),
        'jenkins_jobs.ini')

    conf = None
    if os.path.isfile(local_conf):
        conf = local_conf
    elif os.path.isfile(user_conf):
        conf = user_conf
    elif os.path.isfile(global_conf):
        conf = global_conf

    return conf


JJB_INI = jjb_ini()
