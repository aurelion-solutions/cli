# SPDX-FileCopyrightText: 2026 Michael Abramovich
#
# SPDX-License-Identifier: BUSL-1.1

"""HTTP client wrappers for /api/v0/lake-migrations and /api/v0/lake endpoints."""

from __future__ import annotations

from typing import Any

import httpx
from al.config import DEFAULT_HTTP_TIMEOUT, httpx_client


class LakeMigrationClient:
    """Thin HTTP client for lake migration API endpoints."""

    def __init__(self, base_url: str) -> None:
        self._base = base_url.rstrip("/")

    def start_migration(
        self,
        *,
        dataset: str,
        batch_size: int = 5000,
        resume: str | None = None,
    ) -> Any:
        """POST /api/v0/lake-migrations → response body (dict or list)."""
        url = f"{self._base}/api/v0/lake-migrations"
        params: dict[str, str] = {}
        if resume is not None:
            params["resume"] = resume

        with httpx.Client(timeout=DEFAULT_HTTP_TIMEOUT) as client:
            resp = client.post(
                url,
                json={"dataset": dataset, "batch_size": batch_size},
                params=params,
            )
            resp.raise_for_status()
            return resp.json()

    def get_run(self, run_id: str) -> dict[str, Any]:
        """GET /api/v0/lake-migrations/{run_id}."""
        url = f"{self._base}/api/v0/lake-migrations/{run_id}"
        with httpx.Client(timeout=DEFAULT_HTTP_TIMEOUT) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.json()  # type: ignore[return-value]


class LakeMaintenanceClient:
    """Thin HTTP client for lake maintenance endpoints (/api/v0/lake/...)."""

    def __init__(self, base_url: str) -> None:
        self._base = base_url.rstrip("/")

    def get_status(self) -> dict[str, Any]:
        """GET /api/v0/lake/status → response body."""
        url = f"{self._base}/api/v0/lake/status"
        with httpx_client() as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.json()  # type: ignore[return-value]

    def post_compaction(
        self,
        *,
        table: str,
        retention_days: int,
        orphan_older_than_hours: int,
        target_file_size_mb: int,
    ) -> dict[str, Any]:
        """POST /api/v0/lake/compaction → response body."""
        url = f"{self._base}/api/v0/lake/compaction"
        with httpx_client() as client:
            resp = client.post(
                url,
                json={
                    "table": table,
                    "retention_days": retention_days,
                    "orphan_older_than_hours": orphan_older_than_hours,
                    "target_file_size_mb": target_file_size_mb,
                },
            )
            resp.raise_for_status()
            return resp.json()  # type: ignore[return-value]
