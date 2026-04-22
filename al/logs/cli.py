"""Logs subcommand: read recent platform logs and PostgreSQL log buffer."""

import json
from typing import Any

import httpx
import typer
from al.config import (
    base_url_option,
    handle_connection_error,
    handle_timeout_error,
    httpx_client,
)

app = typer.Typer()


def _buffer_query_params(
    *,
    correlation_id: str | None,
    target_type: str | None,
    target_id: str | None,
    initiator_type: str | None,
    initiator_id: str | None,
    actor_type: str | None,
    actor_id: str | None,
    event_type: str | None,
    level: str | None,
    from_ts: str | None,
    to_ts: str | None,
    order: str,
    limit: int,
) -> dict[str, Any]:
    params: dict[str, Any] = {"order": order, "limit": limit}
    if correlation_id is not None:
        params["correlation_id"] = correlation_id
    if target_type is not None:
        params["target_type"] = target_type
    if target_id is not None:
        params["target_id"] = target_id
    if initiator_type is not None:
        params["initiator_type"] = initiator_type
    if initiator_id is not None:
        params["initiator_id"] = initiator_id
    if actor_type is not None:
        params["actor_type"] = actor_type
    if actor_id is not None:
        params["actor_id"] = actor_id
    if event_type is not None:
        params["event_type"] = event_type
    if level is not None:
        params["level"] = level
    if from_ts is not None:
        params["from_ts"] = from_ts
    if to_ts is not None:
        params["to_ts"] = to_ts
    return params


@app.command("tail")
def tail_(
    limit: int = typer.Option(50, "--limit", help="Max rows (1..500)"),
    level: str | None = typer.Option(
        None, "--level", help="info|warning|error|debug|critical"
    ),
    base_url: str = base_url_option(),
) -> None:
    """Tail recent platform logs from the PostgreSQL log buffer. Outputs JSON array to stdout."""
    url = f"{base_url.rstrip('/')}/api/v0/platform/logs"
    params: dict = {"limit": limit}
    if level is not None:
        params["level"] = level
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


@app.command("read")
def read_(
    limit: int = typer.Option(
        100, "--limit", help="Maximum number of log records to return"
    ),
    base_url: str = base_url_option(),
) -> None:
    """Read recent log records from the platform. Outputs JSON array to stdout."""
    url = f"{base_url.rstrip('/')}/api/v0/logs"
    params = {"limit": limit}
    try:
        with httpx_client() as client:
            response = client.get(url, params=params)
            if response.status_code == 501:
                typer.echo(
                    f"Log read not supported for configured provider: {response.text}",
                    err=True,
                )
                raise typer.Exit(1)
            if response.status_code == 400:
                typer.echo(f"Bad request: {response.text}", err=True)
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


@app.command("buffer")
def buffer_(
    correlation_id: str | None = typer.Option(
        None, "--correlation-id", help="Filter by correlation id"
    ),
    target_type: str | None = typer.Option(
        None, "--target-type", help="With --target-id"
    ),
    target_id: str | None = typer.Option(
        None, "--target-id", help="With --target-type"
    ),
    initiator_type: str | None = typer.Option(
        None, "--initiator-type", help="With --initiator-id"
    ),
    initiator_id: str | None = typer.Option(
        None, "--initiator-id", help="With --initiator-type"
    ),
    actor_type: str | None = typer.Option(None, "--actor-type", help="With --actor-id"),
    actor_id: str | None = typer.Option(None, "--actor-id", help="With --actor-type"),
    event_type: str | None = typer.Option(
        None, "--event-type", help="Exact event_type match"
    ),
    level: str | None = typer.Option(
        None, "--level", help="Log level (e.g. info, error)"
    ),
    from_ts: str | None = typer.Option(
        None,
        "--from-ts",
        help="Inclusive lower bound on event timestamp (ISO 8601)",
    ),
    to_ts: str | None = typer.Option(
        None,
        "--to-ts",
        help="Inclusive upper bound on event timestamp (ISO 8601)",
    ),
    order: str = typer.Option(
        "desc",
        "--order",
        help="Sort by event time: asc (chronological) or desc (newest first)",
    ),
    limit: int = typer.Option(100, "--limit", help="Max rows (1–1000)"),
    base_url: str = base_url_option(),
) -> None:
    """Query the internal PostgreSQL log buffer (debug / trace). Outputs JSON array to stdout."""
    url = f"{base_url.rstrip('/')}/api/v0/log-buffer"
    params = _buffer_query_params(
        correlation_id=correlation_id,
        target_type=target_type,
        target_id=target_id,
        initiator_type=initiator_type,
        initiator_id=initiator_id,
        actor_type=actor_type,
        actor_id=actor_id,
        event_type=event_type,
        level=level,
        from_ts=from_ts,
        to_ts=to_ts,
        order=order,
        limit=limit,
    )
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
