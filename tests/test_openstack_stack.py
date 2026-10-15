# -*- code: utf-8 -*-
# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2026 The Linux Foundation and others.
##############################################################################
"""Unit tests for openstack stack commands."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner
from openstack.orchestration.v1.stack import Stack

from lftools.openstack import cmd, stack


def _stack(stack_id, name, status="CREATE_COMPLETE", age_hours=48):
    """Build a real openstacksdk Stack resource as returned by search_stacks()."""
    created = datetime.now(timezone.utc) - timedelta(hours=age_hours)
    return Stack.existing(
        id=stack_id,
        stack_name=name,
        stack_status=status,
        creation_time=created.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


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

    def test_delete_stale_protects_young_stacks(self, mock_cloud, mock_jenkins):
        """A stack younger than min_age_hours is never reaped.

        get_running_builds() silently drops nodes that 500 or disappear, so an
        unreported build must not cost a live stack its VMs.
        """
        mock_cloud.search_stacks.return_value = [
            _stack("id-young", "releng-job-b-2", age_hours=1),
            _stack("id-old", "releng-job-c-3", age_hours=48),
        ]

        with patch("lftools.openstack.stack.delete") as mock_delete:
            stack.delete_stale("test-cloud", ["https://jenkins.example.org/releng"])

        assert [c.args[1] for c in mock_delete.call_args_list] == ["id-old"]

    def test_delete_stale_skips_unknown_age(self, mock_cloud, mock_jenkins):
        """A stack whose creation time cannot be determined is left alone.

        Covers both reasons an age is unknown: Heat omitted the field
        entirely, and Heat returned a timestamp that will not parse. Either
        way the stack could belong to a running build, so keep it.
        """
        mock_cloud.search_stacks.return_value = [
            Stack.existing(id="id-noage", stack_name="releng-job-b-2", stack_status="CREATE_COMPLETE"),
            Stack.existing(
                id="id-badage",
                stack_name="releng-job-b-3",
                stack_status="CREATE_COMPLETE",
                creation_time="not-a-timestamp",
            ),
        ]

        with patch("lftools.openstack.stack.delete") as mock_delete:
            stack.delete_stale("test-cloud", ["https://jenkins.example.org/releng"])

        mock_delete.assert_not_called()

    def test_delete_stale_honours_custom_min_age(self, mock_cloud, mock_jenkins):
        """The caller-supplied threshold decides, not the module default.

        The stack sits between the custom threshold and the default, so a
        regression that ignored the argument and compared against
        STALE_MIN_AGE_HOURS would keep it and go unnoticed.
        """
        mock_cloud.search_stacks.return_value = [_stack("id-12h", "releng-job-b-2", age_hours=12)]

        with patch("lftools.openstack.stack.delete") as mock_delete:
            stack.delete_stale("test-cloud", ["https://jenkins.example.org/releng"])
        mock_delete.assert_not_called()  # 12h < default 24h

        with patch("lftools.openstack.stack.delete") as mock_delete:
            stack.delete_stale("test-cloud", ["https://jenkins.example.org/releng"], min_age_hours=6)
        assert [c.args[1] for c in mock_delete.call_args_list] == ["id-12h"]

    def test_delete_stale_no_stacks(self, mock_cloud):
        """Exit cleanly when there are no stacks."""
        mock_cloud.search_stacks.return_value = []
        with pytest.raises(SystemExit) as exc_info:
            stack.delete_stale("test-cloud", ["https://jenkins.example.org/releng"])
        assert exc_info.value.code == 0


class TestStackCreate:
    """Test stack create command."""

    @staticmethod
    def _run(mock_cloud, statuses):
        mock_cloud.create_stack.return_value = Stack.existing(id="id-1", stack_name="releng-job-a-1")
        mock_cloud.get_stack.side_effect = [
            Stack.existing(id="id-1", stack_name="releng-job-a-1", stack_status=s) for s in statuses
        ]
        with patch("lftools.openstack.stack.time.sleep"), patch("lftools.openstack.stack.delete", return_value=True):
            stack.create("test-cloud", "releng-job-a-1", "template.yaml", "params.yaml", tries=2)

    def test_create_exits_nonzero_when_all_tries_fail(self, mock_cloud):
        """Quota-exceeded CREATE_FAILED on every try must exit non-zero."""
        with pytest.raises(SystemExit) as exc_info:
            self._run(mock_cloud, ["CREATE_FAILED", "CREATE_FAILED"])
        assert exc_info.value.code == 1

    def test_create_succeeds_without_exit(self, mock_cloud):
        """A successful create returns normally."""
        self._run(mock_cloud, ["CREATE_IN_PROGRESS", "CREATE_COMPLETE"])


@patch("lftools.openstack.stack.delete")
def test_delete_stale_refuses_without_jenkins(mock_delete, mock_cloud):
    """No Jenkins servers means no build list, so every stack would look stale."""
    mock_cloud.search_stacks.return_value = [_stack("id-orphan", "releng-job-b-9")]

    with pytest.raises(SystemExit) as exc_info:
        stack.delete_stale("test-cloud", [])

    assert exc_info.value.code == 1
    mock_delete.assert_not_called()


@patch("lftools.openstack.stack.delete", side_effect=[False, True])
def test_delete_stale_exits_nonzero_when_a_delete_fails(mock_delete, mock_cloud, mock_jenkins, caplog):
    """A stack that will not delete fails the run, after every stack is tried.

    Exiting 0 let the cleanup cron pass while orphans kept consuming quota.
    """
    mock_jenkins.server.get_running_builds.return_value = []
    mock_cloud.search_stacks.return_value = [
        _stack("id-stuck", "releng-job-b-9"),
        _stack("id-orphan", "releng-job-c-8"),
    ]

    with pytest.raises(SystemExit) as exc_info:
        stack.delete_stale("test-cloud", ["https://jenkins.example.org/releng"])

    assert exc_info.value.code == 1
    # Every stack is attempted; the failure is reported only at the end.
    assert [c.args[1] for c in mock_delete.call_args_list] == ["id-stuck", "id-orphan"]
    assert "releng-job-b-9" in caplog.text


def _run_cli(args):
    """Invoke the openstack command group the way the installed CLI does."""
    return CliRunner().invoke(cmd.openstack, ["--os-cloud", "test-cloud"] + args, obj={})


@pytest.mark.parametrize(
    "delete_result,expected",
    [(True, 0), (None, 0), (False, 1)],
    ids=["deleted", "forced", "timed-out"],
)
def test_stack_delete_exit_code(delete_result, expected):
    """A timed-out delete fails the command unless --force asked to ignore it.

    delete() returns True on success, False on timeout, and None when --force
    is set; only False is a failure.
    """
    with patch("lftools.openstack.stack.delete", return_value=delete_result):
        result = _run_cli(["stack", "delete", "a-stack"])

    assert result.exit_code == expected


def test_delete_stale_requires_jenkins_urls():
    """Omitting the Jenkins URLs is a usage error, not a reap-everything run."""
    with patch("lftools.openstack.stack.delete_stale") as mock_delete_stale:
        result = _run_cli(["stack", "delete-stale"])

    assert result.exit_code == 2
    mock_delete_stale.assert_not_called()
