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

import os

JJB_INI = os.path.join(
    os.path.expanduser('~'),
    '.config',
    'jenkins_jobs',
    'jenkins_jobs.ini')
