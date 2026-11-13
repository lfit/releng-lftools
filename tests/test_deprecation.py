# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2026 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Test the lftools deprecation notice."""

from lftools import cli


def test_main_prints_deprecation_notice(mocker, monkeypatch, capsys):
    """The entry point warns on stderr and leaves stdout untouched."""
    monkeypatch.delenv("LFTOOLS_SUPPRESS_DEPRECATION", raising=False)
    group = mocker.patch.object(cli, "cli")

    cli.main()

    captured = capsys.readouterr()
    assert "lftools-uv" in captured.err
    assert captured.out == ""
    group.assert_called_once_with(obj={})


def test_main_deprecation_notice_suppressed(mocker, monkeypatch, capsys):
    """LFTOOLS_SUPPRESS_DEPRECATION=1 silences the notice."""
    monkeypatch.setenv("LFTOOLS_SUPPRESS_DEPRECATION", "1")
    group = mocker.patch.object(cli, "cli")

    cli.main()

    assert capsys.readouterr().err == ""
    group.assert_called_once_with(obj={})
