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
from __future__ import annotations

__author__ = "Thanh Ha"


import logging
import os
import re
import sys
from typing import List, Optional

log: logging.Logger = logging.getLogger(__name__)


def get_header_text(_file: str) -> str:
    """Scan a file and pulls out the license header.

    Returns a string containing the license header with newlines and copyright
    lines stripped.

    Note: This function only supports '#' comments for license headers.
    """
    text: str = ""
    with open(_file, "r") as data:
        lines: List[str] = data.readlines()
        for line in lines:
            result: Optional[re.Match] = re.search(r"\s*[#]", line)
            if not result:
                break
            string: str = re.sub(r"^\s*#+", "", line).strip()
            if bool(re.match("Copyright", string, re.I)) or bool(  # Ignore the Copyright line
                re.match("^#!", line, re.I)
            ):  # Ignore #! shebang lines
                continue
            text += " {}".format(string)
    # Strip unnecessary spacing
    text = re.sub(r"\s+", " ", text).strip()
    return text


def check_license(license_file: str, code_file: str) -> int:
    """Compare a file with the provided license header.

    Reports if license header is missing or does not match the text of
    license_file.
    """
    license_header: str = get_header_text(license_file)
    code_header: str = get_header_text(code_file)

    if license_header not in code_header:
        log.error("{} is missing or has incorrect license header.".format(code_file))
        return 1

    return 0


def check_license_directory(license_file: str, directory: str, regex: str = r".+\.py$") -> None:
    """Search a directory for files and calls check_license()."""
    missing_license: bool = False

    for root, dirs, files in os.walk(directory):
        for f in files:
            if re.search(regex, f):
                if check_license(license_file, os.path.join(root, f)):
                    missing_license = True

    if missing_license:
        sys.exit(1)

    log.info("Scan completed did not detect any files missing license headers.")
