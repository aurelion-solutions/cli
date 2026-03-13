"""NHI subcommand."""

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
    """List all NHIs."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/nhi"
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
    typer.echo(json.dumps(response.json(), indent=2, default=str))


@app.command("get")
def get(
    nhi_id: str = typer.Argument(..., help="NHI ID (UUID)"),
    base_url: str = base_url_option(),
) -> None:
    """Get NHI by id."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/nhi/{nhi_id}"
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
    typer.echo(json.dumps(response.json(), indent=2, default=str))


@app.command("create")
def create(
    external_id: str = typer.Option(..., "--external-id", help="External id"),
    name: str = typer.Option(..., "--name", help="Display name"),
    kind: str = typer.Option(..., "--kind", help="NHI kind"),
    description: str | None = typer.Option(None, "--description"),
    is_locked: bool = typer.Option(False, "--is-locked"),
    owner_employee_id: str | None = typer.Option(
        None, "--owner-employee-id", help="Owner UUID"
    ),
    application_id: str | None = typer.Option(
        None, "--application-id", help="Application UUID"
    ),
    base_url: str = base_url_option(),
) -> None:
    """Create an NHI."""
    import httpx

    body: dict = {
        "external_id": external_id,
        "name": name,
        "kind": kind,
        "is_locked": is_locked,
    }
    if description is not None:
        body["description"] = description
    if owner_employee_id is not None:
        body["owner_employee_id"] = owner_employee_id
    if application_id is not None:
        body["application_id"] = application_id

    url = f"{base_url.rstrip('/')}/api/v0/nhi"
    try:
        with httpx_client() as client:
            response = client.post(url, json=body)
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


@app.command("attributes")
def attributes(
    nhi_id: str = typer.Argument(..., help="NHI ID (UUID)"),
    base_url: str = base_url_option(),
) -> None:
    """List NHI attributes."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/nhi/{nhi_id}/attributes"
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
    typer.echo(json.dumps(response.json(), indent=2, default=str))


@app.command("add-attribute")
def add_attribute(
    nhi_id: str = typer.Argument(..., help="NHI ID (UUID)"),
    key: str = typer.Option(..., "--key"),
    value: str = typer.Option(..., "--value"),
    base_url: str = base_url_option(),
) -> None:
    """Add an attribute to an NHI."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/nhi/{nhi_id}/attributes"
    try:
        with httpx_client() as client:
            response = client.post(url, json={"key": key, "value": value})
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


@app.command("remove-attribute")
def remove_attribute(
    nhi_id: str = typer.Argument(..., help="NHI ID (UUID)"),
    key: str = typer.Argument(..., help="Attribute key"),
    base_url: str = base_url_option(),
) -> None:
    """Remove an attribute from an NHI."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/nhi/{nhi_id}/attributes/{key}"
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
    if response.content:
        typer.echo(json.dumps(response.json(), indent=2, default=str))
