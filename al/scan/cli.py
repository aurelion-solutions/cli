"""Scan-run subcommands."""

import json

import typer

from al.config import (
    base_url_option,
    handle_connection_error,
    handle_timeout_error,
    httpx_client,
)

app = typer.Typer()


@app.command("run")
def run(
    triggered_by: str = typer.Option(
        "manual",
        "--triggered-by",
        help="Trigger mode: manual | api | schedule",
    ),
    scope_subject: str | None = typer.Option(
        None,
        "--scope-subject",
        help="Restrict scan to this subject UUID",
    ),
    scope_application: str | None = typer.Option(
        None,
        "--scope-application",
        help="Restrict scan to this application UUID",
    ),
    created_by: str | None = typer.Option(
        None,
        "--created-by",
        help="Actor identifier recorded on the scan run",
    ),
    base_url: str = base_url_option(),
) -> None:
    """Create a scan run and execute it synchronously. Prints the final ScanRunRead JSON."""
    import httpx

    base = base_url.rstrip("/")
    create_url = f"{base}/api/v0/scan-runs"

    create_body: dict[str, object] = {"triggered_by": triggered_by}
    if scope_subject is not None or scope_application is not None:
        scope: dict[str, object] = {}
        if scope_subject is not None:
            scope["subject_id"] = scope_subject
        if scope_application is not None:
            scope["application_id"] = scope_application
        create_body["scope"] = scope
    if created_by is not None:
        create_body["created_by"] = created_by

    scan_run_id: int | None = None

    try:
        with httpx_client() as client:
            # Step 1 — create pending run
            response_create = client.post(create_url, json=create_body)
            try:
                response_create.raise_for_status()
            except httpx.HTTPStatusError as err:
                if err.response.status_code == 422:
                    typer.echo(f"Validation error: {err.response.text}", err=True)
                else:
                    typer.echo(f"API error: {err.response.text}", err=True)
                raise typer.Exit(1)

            scan_run_id = response_create.json()["id"]

            # Step 2 — execute the run
            run_url = f"{base}/api/v0/scan-runs/{scan_run_id}/run"
            response_run = client.post(run_url)
            try:
                response_run.raise_for_status()
            except httpx.HTTPStatusError as err:
                typer.echo(
                    f"API error (scan run id={scan_run_id}): {err.response.text}",
                    err=True,
                )
                raise typer.Exit(1)

    except httpx.ConnectError:
        handle_connection_error(base_url)
    except httpx.TimeoutException:
        handle_timeout_error(base_url)

    typer.echo(json.dumps(response_run.json(), indent=2, default=str))


@app.command("list")
def list_runs(
    status: str | None = typer.Option(
        None,
        "--status",
        help="Filter by scan run status (pending|running|completed|failed)",
    ),
    triggered_by: str | None = typer.Option(
        None,
        "--triggered-by",
        help="Filter by trigger mode (manual|api|schedule)",
    ),
    scope_subject: str | None = typer.Option(
        None,
        "--scope-subject",
        help="Filter by scoped subject UUID",
    ),
    scope_application: str | None = typer.Option(
        None,
        "--scope-application",
        help="Filter by scoped application UUID",
    ),
    limit: int = typer.Option(50, "--limit", help="Maximum number of results"),
    offset: int = typer.Option(0, "--offset", help="Pagination offset"),
    base_url: str = base_url_option(),
) -> None:
    """List scan runs with optional filters."""
    import httpx

    params: dict[str, str] = {"limit": str(limit), "offset": str(offset)}
    if status is not None:
        params["status"] = status
    if triggered_by is not None:
        params["triggered_by"] = triggered_by
    if scope_subject is not None:
        params["scope_subject_id"] = scope_subject
    if scope_application is not None:
        params["scope_application_id"] = scope_application

    url = f"{base_url.rstrip('/')}/api/v0/scan-runs"
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
