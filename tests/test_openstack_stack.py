# -*- code: utf-8 -*-
# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2026 The Linux Foundation and others.
##############################################################################
"""Unit tests for openstack stack commands."""

from unittest.mock import MagicMock, patch

import pytest
from openstack.orchestration.v1.stack import Stack

from lftools.openstack import stack


def _stack(stack_id, name, status="CREATE_COMPLETE"):
    """Build a real openstacksdk Stack resource as returned by search_stacks()."""
    return Stack.existing(id=stack_id, stack_name=name, stack_status=status)


@pytest.fixture
def mock_cloud():
    """Mock OpenStack cloud connection."""
    with patch("openstack.connection.from_config") as mock:
        cloud = MagicMock()
        mock.return_value = cloud
        yield cloud


@pytest.fixture
def mock_jenkins():
    """Mock Jenkins server reporting one running build."""
    with patch("lftools.openstack.stack.Jenkins") as mock:
        jenkins = MagicMock()
        jenkins.url = "https://jenkins.example.org/releng"
        jenkins.server.get_running_builds.return_value = [{"name": "job-a", "number": 1}]
        mock.return_value = jenkins
        yield jenkins


class TestStackDeleteStale:
    """Test stack delete-stale command."""

    def test_delete_stale_uses_stack_name_and_id(self, mock_cloud, mock_jenkins):
        """Orphaned stacks are deleted by ID; active stacks are kept."""
        mock_cloud.search_stacks.return_value = [
            _stack("id-active", "releng-job-a-1"),
            _stack("id-orphan", "releng-job-b-2"),
            _stack("id-failed", "releng-job-c-3", status="CREATE_FAILED"),
            _stack("id-progress", "releng-job-d-4", status="CREATE_IN_PROGRESS"),
        ]

        with patch("lftools.openstack.stack.delete") as mock_delete:
            stack.delete_stale("test-cloud", ["https://jenkins.example.org/releng"])

        deleted = [c.args[1] for c in mock_delete.call_args_list]
        assert deleted == ["id-orphan", "id-failed"]
        assert None not in deleted

    def test_delete_stale_no_stacks(self, mock_cloud):
        """Exit cleanly when there are no stacks."""
        mock_cloud.search_stacks.return_value = []
        with pytest.raises(SystemExit) as exc_info:
            stack.delete_stale("test-cloud", ["https://jenkins.example.org/releng"])
        assert exc_info.value.code == 0
