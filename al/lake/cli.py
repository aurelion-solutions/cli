# SPDX-FileCopyrightText: 2026 Michael Abramovich
#
# SPDX-License-Identifier: BUSL-1.1

"""Lake management CLI subcommands.

Usage::

    al lake migrate-from-pg [--dataset all|access_artifacts|access_facts]
                            [--batch-size 5000]
                            [--resume <run_id>]
                            [--poll-interval 2.0]

    al lake status [--base-url URL]

    al lake compact [--table all|raw.access_artifacts|normalized.access_facts]
                    [--retention-days N]
                    [--orphan-older-than-hours N]
                    [--target-file-size-mb N]
                    [--base-url URL]
"""

from __future__ import annotations

import json
import time
from enum import Enum
from typing import Any, Optional

import typer
from al.config import (
    base_url_option,
    handle_connection_error,
    handle_timeout_error,
)
from al.lake.api import LakeMaintenanceClient, LakeMigrationClient

app = typer.Typer(help="Data lake management operations.")

_TERMINAL_STATUSES = frozenset({"completed", "failed", "cancelled"})


class CompactionTable(str, Enum):
    """Valid table scope values for the compact command."""

    raw_access_artifacts = "raw.access_artifacts"
    normalized_access_facts = "normalized.access_facts"
    all = "all"


def _print_json(data: Any) -> None:
    """Print data as indented JSON to stdout."""
    typer.echo(json.dumps(data, indent=2))


@app.command("migrate-from-pg")
def migrate_from_pg(
    dataset: str = typer.Option(
        "all",
        "--dataset",
        help="Dataset to migrate: 'all', 'access_artifacts', or 'access_facts'.",
    ),
    batch_size: int = typer.Option(
        5000,
        "--batch-size",
        help="Rows per migration batch.",
    ),
    resume: Optional[str] = typer.Option(
        None,
        "--resume",
        help="Resume an existing run by UUID.",
    ),
    poll_interval: float = typer.Option(
        2.0,
        "--poll-interval",
        help="Seconds between status poll requests.",
    ),
    base_url: str = base_url_option(),
) -> None:
    """Migrate PG access_artifacts and/or access_facts to the Iceberg data lake.

    Calls POST /api/v0/lake-migrations, then polls GET /…/{id} until finished.
    Streams progress to stderr; prints final JSON counts to stdout.
    Exit code 0 on completed, 1 on failure.
    """
    import httpx  # noqa: PLC0415

    client = LakeMigrationClient(base_url=base_url)

    try:
        response = client.start_migration(
            dataset=dataset,
            batch_size=batch_size,
            resume=resume,
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

    # Normalise to list of run dicts.
    runs: list[dict] = response if isinstance(response, list) else [response]
    run_ids = [r["id"] for r in runs]
    typer.echo(f"Started migration run(s): {run_ids}", err=True)

    # Poll until all runs reach terminal status.
    final_runs: dict[str, dict] = {}
    pending_ids = list(run_ids)

    while pending_ids:
        time.sleep(poll_interval)
        still_pending: list[str] = []
        for run_id in pending_ids:
            try:
                run_data = client.get_run(run_id)
            except httpx.ConnectError:
                handle_connection_error(base_url)
                return
            except httpx.HTTPStatusError as err:
                if err.response.status_code == 404:
                    typer.echo(f"Run {run_id} not found.", err=True)
                    raise typer.Exit(1)
                typer.echo(
                    f"Poll error {err.response.status_code}: {err.response.text}",
                    err=True,
                )
                raise typer.Exit(1)

            status = run_data.get("status", "")
            rows_read = run_data.get("rows_read", 0)
            rows_written = run_data.get("rows_written", 0)
            last_id = run_data.get("last_processed_id")

            typer.echo(
                f"  [{run_id[:8]}] status={status} "
                f"rows_read={rows_read} rows_written={rows_written} "
                f"last_id={last_id}",
                err=True,
            )

            if status in _TERMINAL_STATUSES:
                final_runs[run_id] = run_data
            else:
                still_pending.append(run_id)

        pending_ids = still_pending

    # Output final counts as JSON to stdout.
    output = {
        run_id: {
            "status": data.get("status"),
            "rows_read": data.get("rows_read"),
            "rows_written": data.get("rows_written"),
            "dataset": data.get("dataset"),
        }
        for run_id, data in final_runs.items()
    }
    typer.echo(json.dumps(output, indent=2))

    # Exit code: 0 only if all runs completed successfully.
    any_failed = any(
        data.get("status") not in ("completed",) for data in final_runs.values()
    )
    if any_failed:
        raise typer.Exit(1)


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
        help="Skip orphan files newer than this (hours, >=0).",
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
