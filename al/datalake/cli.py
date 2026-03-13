"""Data lake subcommand: batches and related operations."""

import json

import typer

from al.config import (
    base_url_option,
    handle_connection_error,
    handle_timeout_error,
    httpx_client,
)

app = typer.Typer()
batches = typer.Typer()
app.add_typer(batches, name="batches")


@batches.command("create")
def create(
    storage_provider: str = typer.Option(
        ..., "--storage-provider", help="Storage provider (e.g. file)"
    ),
    dataset_type: str = typer.Option(
        ..., "--dataset-type", help="Dataset type (e.g. accounts)"
    ),
    records: str = typer.Option(
        ..., "--records", help='Records as JSON array (e.g. \'[{"id":"1"}]\')'
    ),
    task_id: str | None = typer.Option(
        None, "--task-id", help="Optional task ID (UUID)"
    ),
    application_id: str | None = typer.Option(
        None, "--application-id", help="Optional application ID (UUID)"
    ),
    base_url: str = base_url_option(),
) -> None:
    """Create a lake batch: write records to lake."""
    import httpx

    try:
        records_list = json.loads(records)
        if not isinstance(records_list, list):
            raise ValueError("records must be a JSON array")
    except json.JSONDecodeError as err:
        typer.echo(f"Invalid --records JSON: {err}", err=True)
        raise typer.Exit(1)
    except ValueError as err:
        typer.echo(str(err), err=True)
        raise typer.Exit(1)

    payload = {
        "storage_provider": storage_provider,
        "dataset_type": dataset_type,
        "records": records_list,
        "task_id": task_id,
        "application_id": application_id,
    }
    payload = {k: v for k, v in payload.items() if v is not None}

    url = f"{base_url.rstrip('/')}/api/v0/datalake/batches"
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
    typer.echo(f"Created lake batch {result['id']}")
    typer.echo(f"  storage_provider: {result['storage_provider']}")
    typer.echo(f"  dataset_type: {result['dataset_type']}")
    typer.echo(f"  row_count: {result['row_count']}")


@batches.command("get")
def get(
    batch_id: str = typer.Argument(..., help="Batch ID (UUID)"),
    base_url: str = base_url_option(),
) -> None:
    """Get lake batch metadata."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/datalake/batches/{batch_id}"
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


@batches.command("data")
def data(
    batch_id: str = typer.Argument(..., help="Batch ID (UUID)"),
    base_url: str = base_url_option(),
) -> None:
    """Get lake batch payload (records)."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/datalake/batches/{batch_id}/data"
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


@batches.command("delete")
def delete(
    batch_id: str = typer.Argument(..., help="Batch ID (UUID)"),
    base_url: str = base_url_option(),
) -> None:
    """Delete lake batch (metadata and payload)."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/datalake/batches/{batch_id}"
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
    typer.echo("Lake batch deleted")
