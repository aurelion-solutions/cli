# SPDX-FileCopyrightText: 2026 Michael Abramovich
#
# SPDX-License-Identifier: BUSL-1.1

"""Lake management CLI subcommands.

Usage::

    al lake status [--base-url URL]

    al lake compact [--table all|raw.access_artifacts|normalized.access_facts]
                    [--retention-days N]
                    [--orphan-older-than-hours N]
                    [--target-file-size-mb N]
                    [--base-url URL]
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Any

import typer
from al.config import (
    base_url_option,
    handle_connection_error,
    handle_timeout_error,
)
from al.lake.api import LakeMaintenanceClient

app = typer.Typer(help="Data lake management operations.")


class CompactionTable(str, Enum):
    """Valid table scope values for the compact command."""

    raw_access_artifacts = "raw.access_artifacts"
    normalized_access_facts = "normalized.access_facts"
    all = "all"


def _print_json(data: Any) -> None:
    """Print data as indented JSON to stdout."""
    typer.echo(json.dumps(data, indent=2))


@app.command("status")
def status(
    base_url: str = base_url_option(),
) -> None:
    """Show data lake catalog/warehouse status and per-table snapshot metadata.

    Calls GET /api/v0/lake/status. Prints the JSON body to stdout.
    Exit 0 on 2xx; 1 on connection / timeout / non-2xx.
    """
    import httpx  # noqa: PLC0415

    client = LakeMaintenanceClient(base_url=base_url)

    try:
        data = client.get_status()
    except httpx.ConnectError:
        handle_connection_error(base_url)
        return
    except httpx.TimeoutException:
        handle_timeout_error(base_url)
        return
    except httpx.HTTPStatusError as err:
        typer.echo(
            f"API error {err.response.status_code}: {err.response.text}",
            err=True,
        )
        raise typer.Exit(1)

    _print_json(data)


@app.command("compact")
def compact(
    table: CompactionTable = typer.Option(
        CompactionTable.all,
        "--table",
        help="Table scope: raw.access_artifacts, normalized.access_facts, or all.",
        case_sensitive=False,
    ),
    retention_days: int = typer.Option(
        7,
        "--retention-days",
        min=0,
        help="Snapshot retention window in days (>=0).",
    ),
    orphan_older_than_hours: int = typer.Option(
        24,
        "--orphan-older-than-hours",
        min=0,
        help="Skip orphan files newer than this age (hours, >=0).",
    ),
    target_file_size_mb: int = typer.Option(
        128,
        "--target-file-size-mb",
        min=1,
        help="Target compacted file size in MB (>=1).",
    ),
    base_url: str = base_url_option(),
) -> None:
    """Run lake compaction + snapshot expiry + (gated) orphan cleanup.

    Calls POST /api/v0/lake/compaction. Prints the JSON body to stdout.
    Exit 0 on 2xx; 1 on connection / timeout / non-2xx.
    """
    import httpx  # noqa: PLC0415

    client = LakeMaintenanceClient(base_url=base_url)

    try:
        data = client.post_compaction(
            table=table.value,
            retention_days=retention_days,
            orphan_older_than_hours=orphan_older_than_hours,
            target_file_size_mb=target_file_size_mb,
        )
    except httpx.ConnectError:
        handle_connection_error(base_url)
        return
    except httpx.TimeoutException:
        handle_timeout_error(base_url)
        return
    except httpx.HTTPStatusError as err:
        typer.echo(
            f"API error {err.response.status_code}: {err.response.text}",
            err=True,
        )
        raise typer.Exit(1)

    _print_json(data)
