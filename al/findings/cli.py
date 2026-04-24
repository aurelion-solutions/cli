"""Findings subcommands."""

import json

import typer

from al.config import (
    base_url_option,
    handle_connection_error,
    handle_timeout_error,
    httpx_client,
)

app = typer.Typer()


@app.command("list")
def list_findings(
    scan_run: int | None = typer.Option(
        None,
        "--scan-run",
        help="Filter by scan run ID",
    ),
    rule: int | None = typer.Option(
        None,
        "--rule",
        help="Filter by SoD rule ID",
    ),
    severity: str | None = typer.Option(
        None,
        "--severity",
        help="Filter by severity (critical|high|medium|low|informational)",
    ),
    status: str | None = typer.Option(
        None,
        "--status",
        help="Filter by status (open|acknowledged|resolved|mitigated)",
    ),
    kind: str | None = typer.Option(
        None,
        "--kind",
        help="Filter by kind (sod|orphan_access|terminated_access|unused_access)",
    ),
    subject: str | None = typer.Option(
        None,
        "--subject",
        help="Filter by subject UUID",
    ),
    limit: int = typer.Option(50, "--limit", help="Maximum number of results"),
    offset: int = typer.Option(0, "--offset", help="Pagination offset"),
    base_url: str = base_url_option(),
) -> None:
    """List findings with optional audit-style filters."""
    import httpx

    params: dict[str, str] = {"limit": str(limit), "offset": str(offset)}
    if scan_run is not None:
        params["scan_run_id"] = str(scan_run)
    if rule is not None:
        params["rule_id"] = str(rule)
    if severity is not None:
        params["severity"] = severity
    if status is not None:
        params["status"] = status
    if kind is not None:
        params["kind"] = kind
    if subject is not None:
        params["subject_id"] = subject

    url = f"{base_url.rstrip('/')}/api/v0/findings"
    try:
        with httpx_client() as client:
            response = client.get(url, params=params)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as err:
                typer.echo(f"API error: {err.response.text}", err=True)
                raise typer.Exit(1)
    except httpx.ConnectError:
        handle_connection_error(base_url)
    except httpx.TimeoutException:
        handle_timeout_error(base_url)

    typer.echo(json.dumps(response.json(), indent=2, default=str))
