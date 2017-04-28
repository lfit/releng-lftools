# -*- code: utf-8 -*-
"""Github tools test module"""
# @License EPL-1.0 <http://spdx.org/licenses/EPL-1.0>
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################

from lftools.github import cmd as githubcmd

def test_get_repo():
    '''
    Test to get github repository object.
    '''
    repo = githubcmd.get_user().get_repo()
    assert repo
