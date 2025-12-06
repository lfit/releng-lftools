# -*- code: utf-8 -*-
# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2025 The Linux Foundation and others.
##############################################################################
"""Unit tests for openstack cluster commands."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from lftools.openstack import cluster


@pytest.fixture
def mock_cloud():
    """Mock OpenStack cloud connection."""
    with patch("openstack.connection.from_config") as mock:
        cloud = MagicMock()
        mock.return_value = cloud
        yield cloud


@pytest.fixture
def sample_clusters():
    """Sample cluster data for testing."""
    clusters = []

    # Old cluster (30 days old)
    old_cluster = MagicMock()
    old_cluster.name = "old-cluster-001"
    old_cluster.uuid = "uuid-old-001"
    old_cluster.created_at = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    clusters.append(old_cluster)

    # Recent cluster (1 day old)
    new_cluster = MagicMock()
    new_cluster.name = "new-cluster-001"
    new_cluster.uuid = "uuid-new-001"
    new_cluster.created_at = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    clusters.append(new_cluster)

    return clusters


class TestClusterFilter:
    """Test cluster filtering functionality."""

    def test_filter_clusters_no_filter(self, sample_clusters):
        """Test filtering with no days filter returns all clusters."""
        result = cluster._filter_clusters(sample_clusters, days=0)
        assert len(result) == 2

    def test_filter_clusters_with_days(self, sample_clusters):
        """Test filtering clusters older than specified days."""
        result = cluster._filter_clusters(sample_clusters, days=7)
        assert len(result) == 1
        assert result[0].name == "old-cluster-001"


class TestClusterList:
    """Test cluster list command."""

    def test_list_clusters(self, mock_cloud, sample_clusters, caplog):
        """Test listing clusters."""
        mock_cloud.list_coe_clusters.return_value = sample_clusters
        cluster.list("test-cloud", days=0)
        assert "old-cluster-001" in caplog.text
        assert "new-cluster-001" in caplog.text

    def test_list_clusters_with_filter(self, mock_cloud, sample_clusters, caplog):
        """Test listing clusters with days filter."""
        mock_cloud.list_coe_clusters.return_value = sample_clusters
        cluster.list("test-cloud", days=7)
        assert "old-cluster-001" in caplog.text
        assert "new-cluster-001" not in caplog.text


class TestClusterCleanup:
    """Test cluster cleanup command."""

    def test_cleanup_clusters(self, mock_cloud, sample_clusters, caplog):
        """Test cleanup of old clusters."""
        import logging

        caplog.set_level(logging.INFO)
        mock_cloud.list_coe_clusters.return_value = sample_clusters
        mock_cloud.cloud_config.name = "test-cloud"
        mock_cloud.delete_coe_cluster.return_value = True
        cluster.cleanup("test-cloud", days=7)
        mock_cloud.delete_coe_cluster.assert_called_once_with("uuid-old-001")
        assert "Removing 1 clusters" in caplog.text


class TestClusterRemove:
    """Test cluster remove command."""

    def test_remove_cluster_found(self, mock_cloud, sample_clusters):
        """Test removing an existing cluster."""
        mock_cloud.get_coe_cluster.return_value = sample_clusters[0]
        mock_cloud.delete_coe_cluster.return_value = True
        cluster.remove("test-cloud", "old-cluster-001", minutes=0)
        mock_cloud.delete_coe_cluster.assert_called_once_with("uuid-old-001")

    def test_remove_cluster_not_found(self, mock_cloud):
        """Test removing non-existent cluster."""
        mock_cloud.get_coe_cluster.return_value = None
        with pytest.raises(SystemExit) as exc_info:
            cluster.remove("test-cloud", "nonexistent-cluster", minutes=0)
        assert exc_info.value.code == 1


class TestClusterShow:
    """Test cluster show command."""

    def test_show_cluster_found(self, mock_cloud, sample_clusters):
        """Test showing cluster details."""
        mock_cloud.get_coe_cluster.return_value = sample_clusters[0]
        cluster.show("test-cloud", "old-cluster-001")
        mock_cloud.pprint.assert_called_once()

    def test_show_cluster_not_found(self, mock_cloud):
        """Test showing non-existent cluster."""
        mock_cloud.get_coe_cluster.return_value = None
        with pytest.raises(SystemExit) as exc_info:
            cluster.show("test-cloud", "nonexistent-cluster")
        assert exc_info.value.code == 1
