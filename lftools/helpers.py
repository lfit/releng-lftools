# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2020 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################

"""Nexus3 REST API interface."""

import random
import string


def generate_password(length=12):
    punctuation = "!#$%&()*+,-.:;<=>?@[]^_{|}~"
    password_characters = string.ascii_letters + string.digits + punctuation
    return "".join(random.choice(password_characters) for _ in range(length))
