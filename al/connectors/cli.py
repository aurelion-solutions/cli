"""Connector instance subcommands (instances registered with the platform API)."""

import json

import typer

from al.config import (
    base_url_option,
    handle_connection_error,
    handle_timeout_error,
    httpx_client,
)

app = typer.Typer(help="List and inspect connector instances registered with the API.")


@app.command("list")
def list_cmd(
    base_url: str = base_url_option(),
    as_json: bool = typer.Option(False, "--json", help="Print raw JSON response"),
):
    """List all connector instances."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/connector-instances"
    try:
        with httpx_client() as client:
            response = client.get(url)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as err:
                typer.echo(f"API error: {err.response.text}", err=True)
                raise typer.Exit(1)
    except httpx.ConnectError:
        handle_connection_error(base_url)
    except httpx.TimeoutException:
        handle_timeout_error(base_url)

    data = response.json()
    if as_json:
        typer.echo(json.dumps(data, indent=2, default=str))
        return

    if not data:
        typer.echo("No connector instances")
        return

    for r in data:
        tags = ",".join(r.get("tags") or [])
        online = "online" if r.get("is_online") else "offline"
        typer.echo(
            f"{r['instance_id']}\t{online}\t[{tags}]\tlast_seen={r.get('last_seen_at')}"
        )


@app.command("get")
def get_cmd(
    instance_id: str = typer.Argument(..., help="Instance id (e.g. runtime-a)"),
    base_url: str = base_url_option(),
    as_json: bool = typer.Option(False, "--json", help="Print raw JSON response"),
):
    """Show one connector instance by id."""
    import httpx

    rid = instance_id.strip()
    url = f"{base_url.rstrip('/')}/api/v0/connector-instances/{rid}"
    try:
        with httpx_client() as client:
            response = client.get(url)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as err:
                if err.response.status_code == 404:
                    typer.echo(f"Connector instance not found: {rid}", err=True)
                    raise typer.Exit(1)
                typer.echo(f"API error: {err.response.text}", err=True)
                raise typer.Exit(1)
    except httpx.ConnectError:
        handle_connection_error(base_url)
    except httpx.TimeoutException:
        handle_timeout_error(base_url)

    r = response.json()
    if as_json:
        typer.echo(json.dumps(r, indent=2, default=str))
        return

    tags = ", ".join(r.get("tags") or [])
    online = "online" if r.get("is_online") else "offline"
    typer.echo(f"instance_id:  {r['instance_id']}")
    typer.echo(f"id:           {r['id']}")
    typer.echo(f"status:       {online}")
    typer.echo(f"tags:         [{tags}]")
    typer.echo(f"last_seen:    {r.get('last_seen_at')}")
    typer.echo(f"created_at:   {r.get('created_at')}")
    typer.echo(f"updated_at:   {r.get('updated_at')}")
