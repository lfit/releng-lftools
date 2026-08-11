# -*- code: utf-8 -*-
# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2026 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Unit tests for openstack image commands."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from lftools.openstack import image


def _make_image(name, image_id, days_old=365):
    """Build a stale, ci_managed, deletable image mock."""
    img = MagicMock()
    img.name = name
    img.id = image_id
    img.is_protected = False
    img.visibility = "private"
    img.owner = "project-1"
    img.properties = {"ci_managed": "yes"}
    img.created_at = (datetime.now() - timedelta(days=days_old)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return img


@pytest.fixture
def mock_cloud():
    """Mock OpenStack cloud connection."""
    with patch("openstack.connection.from_config") as mock:
        cloud = MagicMock()
        cloud.config._name = "vex"
        cloud._get_project_info.return_value = {"id": "project-1"}
        cloud.delete_image.return_value = True
        mock.return_value = cloud
        yield cloud


def test_cleanup_deletes_duplicate_names_by_id(mock_cloud):
    """Images sharing a name must still be deleted, addressed by unique id.

    Regression: deleting by name raised DuplicateResource for every image
    whose name was not unique, so those images were skipped on every run and
    accumulated in the cloud forever.
    """
    mock_cloud.list_images.return_value = [
        _make_image("ubuntu-2204-builder-2025-11-06-0835", "id-dup-a"),
        _make_image("ubuntu-2204-builder-2025-11-06-0835", "id-dup-b"),
        _make_image("ubuntu-2204-builder-2025-10-21-0304", "id-unique"),
    ]

    image.cleanup("vex", days=180)

    deleted = [call.args[0] for call in mock_cloud.delete_image.call_args_list]
    assert deleted == ["id-dup-a", "id-dup-b", "id-unique"]


def test_cleanup_skips_protected_and_foreign_images(mock_cloud):
    """Protected, shared and other-project images must never be deleted."""
    protected = _make_image("protected", "id-protected")
    protected.is_protected = True
    shared = _make_image("shared", "id-shared")
    shared.visibility = "shared"
    foreign = _make_image("foreign", "id-foreign")
    foreign.owner = "project-2"
    keeper = _make_image("recent", "id-recent", days_old=1)

    mock_cloud.list_images.return_value = [
        protected,
        shared,
        foreign,
        keeper,
        _make_image("stale", "id-stale"),
    ]

    image.cleanup("vex", days=180)

    deleted = [call.args[0] for call in mock_cloud.delete_image.call_args_list]
    assert deleted == ["id-stale"]
