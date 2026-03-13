"""Employee subcommand: read-only operations."""

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
def list_(
    base_url: str = base_url_option(),
) -> None:
    """List all employees."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/employees"
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
    result = response.json()
    typer.echo(json.dumps(result, indent=2, default=str))


@app.command("get")
def get(
    employee_id: str = typer.Argument(..., help="Employee ID (UUID)"),
    base_url: str = base_url_option(),
) -> None:
    """Get employee by id."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/employees/{employee_id}"
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
    result = response.json()
    typer.echo(json.dumps(result, indent=2, default=str))


@app.command("attributes")
def attributes(
    employee_id: str = typer.Argument(..., help="Employee ID (UUID)"),
    base_url: str = base_url_option(),
) -> None:
    """List employee attributes."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/employees/{employee_id}/attributes"
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
    result = response.json()
    typer.echo(json.dumps(result, indent=2, default=str))
