"""App subcommand for application operations."""

import json

import typer
from al.config import (
    base_url_option,
    handle_connection_error,
    handle_timeout_error,
    httpx_client,
)
from al.connectors.cli import app as connectors_app

app = typer.Typer()

reconcile = typer.Typer()

app.add_typer(reconcile, name="reconcile")
app.add_typer(connectors_app, name="connectors")


@app.command("create")
def create(
    name: str = typer.Option(..., "--name", help="Application name"),
    code: str = typer.Option(
        ...,
        "--code",
        help="Short stable identifier (lowercase a-z0-9_-, 1-64 chars). Passed to PDP as target.application.",
    ),
    config: str = typer.Option("{}", "--config", help="Config as JSON object"),
    required_tags: str = typer.Option(
        "[]",
        "--required-tags",
        help='Tags used to select a connector instance, JSON array, e.g. \'["prod","hr"]\'',
    ),
    inactive: bool = typer.Option(
        False,
        "--inactive",
        help="Create application as inactive (default: active)",
    ),
    base_url: str = base_url_option(),
):
    """Create an application."""
    import httpx

    try:
        config_dict = json.loads(config) if config else {}
    except json.JSONDecodeError as err:
        typer.echo(f"Invalid --config JSON: {err}", err=True)
        raise typer.Exit(1)
    try:
        tags_list = json.loads(required_tags) if required_tags else []
    except json.JSONDecodeError as err:
        typer.echo(f"Invalid --required-tags JSON: {err}", err=True)
        raise typer.Exit(1)
    if not isinstance(tags_list, list):
        typer.echo("--required-tags must be a JSON array", err=True)
        raise typer.Exit(1)
    url = f"{base_url.rstrip('/')}/api/v0/applications"
    payload = {
        "name": name,
        "code": code,
        "config": config_dict,
        "required_connector_tags": tags_list,
        "is_active": not inactive,
    }
    try:
        with httpx_client() as client:
            response = client.post(url, json=payload)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as err:
                typer.echo(f"API error: {err.response.text}", err=True)
                raise typer.Exit(1)
    except httpx.ConnectError:
        handle_connection_error(base_url)
    except httpx.TimeoutException:
        handle_timeout_error(base_url)
    result = response.json()
    typer.echo(f"Created application {result['id']}")
    typer.echo(f"  name: {result['name']}")
    typer.echo(f"  code: {result['code']}")
    typer.echo(f"  required_connector_tags: {result['required_connector_tags']}")
    typer.echo(f"  is_active: {result['is_active']}")


@app.command("list")
def list_cmd(
    base_url: str = base_url_option(),
):
    """List applications."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/applications"
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
    apps = response.json()
    if not apps:
        typer.echo("No applications")
        return
    for a in apps:
        tags = ",".join(a.get("required_connector_tags") or [])
        typer.echo(
            f"{a['id']}  {a['name']}  [{tags}]  "
            f"{'active' if a['is_active'] else 'inactive'}"
        )


@app.command("delete")
def delete(
    app_id: str = typer.Option(..., "--app-id", help="Application ID to delete"),
    base_url: str = base_url_option(),
):
    """Delete an application."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/applications/{app_id}"
    try:
        with httpx_client() as client:
            response = client.delete(url)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as err:
                typer.echo(f"API error: {err.response.text}", err=True)
                raise typer.Exit(1)
    except httpx.ConnectError:
        handle_connection_error(base_url)
    except httpx.TimeoutException:
        handle_timeout_error(base_url)
    typer.echo("Application deleted")


@reconcile.command("run")
def run(
    app_id: str = typer.Option(..., "--app-id", help="Application ID to reconcile"),
    base_url: str = base_url_option(),
):
    """Trigger reconciliation for an application."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/applications/{app_id}/reconcile"
    try:
        with httpx_client() as client:
            response = client.post(url)
            response.raise_for_status()
    except httpx.ConnectError:
        handle_connection_error(base_url)
    except httpx.TimeoutException:
        handle_timeout_error(base_url)
    result = response.json()
    if response.status_code == 202:
        typer.echo(
            f"Reconciliation started for application {result.get('application_id', app_id)}"
        )
        typer.echo(f"  correlation_id: {result.get('correlation_id', '')}")
        typer.echo("  Follow progress in platform logs / log buffer.")
    else:
        typer.echo(f"Reconciled application {result['application_id']}")
        typer.echo(f"  Accounts: {result['accounts']}")
