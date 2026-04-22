"""Events subcommand: tail recent domain events from the platform ring buffer."""

import json

import httpx
import typer
from al.config import (
    base_url_option,
    handle_connection_error,
    handle_timeout_error,
    httpx_client,
)

app = typer.Typer()


@app.command("tail")
def tail_(
    limit: int = typer.Option(50, "--limit", help="Max rows (1..500)"),
    base_url: str = base_url_option(),
) -> None:
    """Tail recent domain events from the in-memory ring buffer. Outputs JSON array to stdout."""
    url = f"{base_url.rstrip('/')}/api/v0/platform/events"
    params: dict = {"limit": limit}
    try:
        with httpx_client() as client:
            response = client.get(url, params=params)
            if response.status_code in (400, 422):
                detail = response.text
                try:
                    body = response.json()
                    if isinstance(body, dict) and "detail" in body:
                        detail = body["detail"]
                        if isinstance(detail, list):
                            detail = json.dumps(detail)
                except json.JSONDecodeError:
                    pass
                typer.echo(
                    f"Request failed ({response.status_code}): {detail}", err=True
                )
                raise typer.Exit(1)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as err:
                typer.echo(f"API error: {err.response.text}", err=True)
                raise typer.Exit(1)
            records = response.json()
    except httpx.ConnectError:
        handle_connection_error(base_url)
    except httpx.TimeoutException:
        handle_timeout_error(base_url)
    if not isinstance(records, list):
        typer.echo("Unexpected API response", err=True)
        raise typer.Exit(1)
    typer.echo(json.dumps(records, indent=2, default=str))
