"""Reconciliation subcommand for al CLI."""

from uuid import UUID

import typer
from al.config import (
    base_url_option,
    handle_connection_error,
    handle_timeout_error,
    httpx_client,
)

app = typer.Typer(help="Artifact-first reconciliation operations.")


@app.command("run")
def run(
    application_id: UUID = typer.Option(
        ..., "--application-id", help="Application UUID to reconcile"
    ),
    base_url: str = base_url_option(),
):
    """Trigger a reconciliation run for the given application.

    POSTs to /api/v0/reconciliation/runs and displays the eight-field summary.
    Exit code 0 on success, non-zero on error.
    """
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/reconciliation/runs"
    payload = {"application_id": str(application_id)}

    try:
        with httpx_client() as client:
            response = client.post(url, json=payload)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as err:
                if err.response.status_code == 404:
                    typer.echo("Application not found", err=True)
                else:
                    typer.echo(
                        f"API error {err.response.status_code}: {err.response.text}",
                        err=True,
                    )
                raise typer.Exit(1)
    except httpx.ConnectError:
        handle_connection_error(base_url)
    except httpx.TimeoutException:
        handle_timeout_error(base_url)

    result = response.json()

    typer.echo(
        f"Reconciliation completed for application {result.get('application_id')}"
    )
    typer.echo(f"  started_at:          {result.get('started_at')}")
    typer.echo(f"  finished_at:         {result.get('finished_at')}")
    typer.echo(f"  artifacts_ingested:  {result.get('artifacts_ingested')}")
    typer.echo(f"  facts_created:       {result.get('facts_created')}")
    typer.echo(f"  facts_updated:       {result.get('facts_updated')}")
    typer.echo(f"  facts_revoked:       {result.get('facts_revoked')}")
    typer.echo(f"  artifacts_unhandled: {result.get('artifacts_unhandled')}")
