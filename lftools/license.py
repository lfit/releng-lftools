# -*- coding: utf-8 -*-
# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2017 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Scans code for a valid license header."""

__author__ = 'Thanh Ha'


import os
import re
import sys


def get_header_text(_file):
    """Scan a file and pulls out the license header.

    Returns a string containing the license header with newlines and copyright
    lines stripped.

    Note: This function only supports '#' comments for license headers.
    """
    text = ''
    with open(_file, 'r') as data:
        lines = data.readlines()
        for line in lines:
            result = re.search(r'\s*[#]', line)
            if not result:
                break
            string = re.sub(r'^\s*#+', '', line).strip()
            if bool(re.match('Copyright', string, re.I)):  # Ignore the Copyright line
                continue
            text += ' {}'.format(string)
    # Strip unnecessary spacing
    text = re.sub('\s+', ' ', text).strip()
    return text


def check_license(license_file, code_file):
    """Compare a file with the provided license header.

    Reports if license header is missing or does not match the text of
    license_file.
    """
    license_header = get_header_text(license_file)
    code_header = get_header_text(code_file)

    if not license_header in code_header:
        print('ERROR: {} is missing or has incorrect license header.'.format(code_file))
        return 1

    return 0


def check_license_directory(license_file, directory, extension="py"):
    """Searches a directory for files and calls check_license()"""

    missing_license = False

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".{}".format(extension)):
                if check_license(license_file, os.path.join(root, file)):
                    missing_license = True

    if not missing_license:
        print('Scan completed did not detect any files missing license headers.')
