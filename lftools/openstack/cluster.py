# -*- code: utf-8 -*-
# SPDX-License-Identifier: EPL-1.0
##############################################################################
# Copyright (c) 2025 The Linux Foundation and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
##############################################################################
"""Cluster related sub-commands for openstack command."""

__author__ = "Anil Belur"

import json
import subprocess
import sys


def _fetch_jenkins_builds(jenkins_urls):
    """Fetch active builds from Jenkins URLs.

    :arg list jenkins_urls: List of Jenkins URLs to check.
    :returns: List of active build identifiers (silo-job-build format).
    """
    builds = []

    for jenkins in jenkins_urls:
        jenkins = jenkins.rstrip("/")
        params = "tree=computer[executors[currentExecutable[url]],oneOffExecutors[currentExecutable[url]]]"
        params += "&xpath=//url&wrapper=builds"
        jenkins_url = f"{jenkins}/computer/api/json?{params}"

        try:
            # Use curl to fetch data
            result = subprocess.run(
                [
                    "curl",
                    "-s",
                    "-w",
                    "\\n\\n%{http_code}",
                    "--globoff",
                    "-H",
                    "Content-Type:application/json",
                    jenkins_url,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            lines = result.stdout.strip().split("\n")
            if len(lines) < 2:
                print(f"ERROR: Invalid response from {jenkins_url}")
                continue

            status = lines[-1]
            json_data = "\n".join(lines[:-2])

            if status != "200":
                print(f"ERROR: Failed to fetch data from {jenkins_url} with status code {status}")
                continue

            # Determine silo name
            if "jenkins." in jenkins and (".org" in jenkins or ".io" in jenkins):
                silo = "production"
            else:
                silo = jenkins.split("/")[-1]

            # Parse JSON and extract build identifiers
            data = json.loads(json_data)
            for computer in data.get("computer", []):
                for executor in computer.get("executors", []) + computer.get("oneOffExecutors", []):
                    current_exec = executor.get("currentExecutable", {})
                    url = current_exec.get("url")
                    if url and url != "null":
                        parts = url.rstrip("/").split("/")
                        if len(parts) >= 2:
                            job_name = parts[-2]
                            build_num = parts[-1]
                            builds.append(f"{silo}-{job_name}-{build_num}")

        except subprocess.TimeoutExpired:
            print(f"ERROR: Timeout fetching data from {jenkins_url}")
        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to parse JSON from {jenkins_url}: {e}")
        except Exception as e:
            print(f"ERROR: Unexpected error fetching from {jenkins_url}: {e}")

    return builds


def _cluster_in_jenkins(cluster_name, jenkins_builds):
    """Check if cluster is in active Jenkins builds.

    :arg str cluster_name: Name of the cluster to check.
    :arg list jenkins_builds: List of active build identifiers.
    :returns: True if cluster is in use, False otherwise.
    """
    return cluster_name in " ".join(jenkins_builds)


def list(os_cloud):
    """List COE clusters.

    :arg str os_cloud: Cloud name as defined in OpenStack clouds.yaml.
    """
    try:
        result = subprocess.run(
            [
                "openstack",
                "--os-cloud",
                os_cloud,
                "coe",
                "cluster",
                "list",
                "-f",
                "value",
                "-c",
                "uuid",
                "-c",
                "name",
                "-c",
                "status",
                "-c",
                "health_status",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split()
                if len(parts) >= 2:
                    print(parts[1])  # Print cluster name

    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to list clusters: {e.stderr}")
        sys.exit(1)


def cleanup(os_cloud, jenkins_urls=None):
    """Remove orphaned COE clusters from cloud.

    Scans for COE clusters not in use by active Jenkins builds and removes them.
    Clusters with names containing '-managed-prod-k8s-' or '-managed-test-k8s-'
    are preserved as they are long-lived managed clusters.

    :arg str os_cloud: Cloud name as defined in OpenStack clouds.yaml.
    :arg str jenkins_urls: Space-separated list of Jenkins URLs to check for active builds.
    """
    # Parse Jenkins URLs
    jenkins_url_list = []
    if jenkins_urls:
        jenkins_url_list = [url.strip() for url in jenkins_urls.split() if url.strip()]

    if not jenkins_url_list:
        print("WARN: No Jenkins URLs provided, skipping cluster cleanup to be safe")
        return

    print(f"INFO: Checking Jenkins URLs for active builds: {' '.join(jenkins_url_list)}")

    # Fetch active builds from Jenkins
    active_builds = _fetch_jenkins_builds(jenkins_url_list)
    print(f"INFO: Found {len(active_builds)} active builds in Jenkins")

    # Fetch COE cluster list
    try:
        result = subprocess.run(
            [
                "openstack",
                "--os-cloud",
                os_cloud,
                "coe",
                "cluster",
                "list",
                "-f",
                "value",
                "-c",
                "uuid",
                "-c",
                "name",
                "-c",
                "status",
                "-c",
                "health_status",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        clusters = []
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split()
                if len(parts) >= 2:
                    clusters.append(parts[1])  # cluster name

        print(f"INFO: Found {len(clusters)} COE clusters on cloud {os_cloud}")

        # Delete orphaned clusters
        deleted_count = 0
        for cluster_name in clusters:
            # Check if cluster is managed (long-lived)
            if "-managed-prod-k8s-" in cluster_name or "-managed-test-k8s-" in cluster_name:
                print(f"INFO: Skipping managed cluster: {cluster_name}")
                continue

            # Check if cluster is in active Jenkins builds
            if _cluster_in_jenkins(cluster_name, active_builds):
                print(f"INFO: Cluster {cluster_name} is in use by active build, skipping")
                continue

            # Delete orphaned cluster
            print(f"INFO: Deleting orphaned k8s cluster: {cluster_name}")
            try:
                subprocess.run(
                    ["openstack", "--os-cloud", os_cloud, "coe", "cluster", "delete", cluster_name],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                deleted_count += 1
                print(f"INFO: Successfully deleted cluster: {cluster_name}")
            except subprocess.CalledProcessError as e:
                print(f"ERROR: Failed to delete cluster {cluster_name}: {e.stderr}")

        print(f"INFO: Deleted {deleted_count} orphaned cluster(s)")

    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to list clusters: {e.stderr}")
        sys.exit(1)
