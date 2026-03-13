"""Policy subcommand."""

import json
import sys
from pathlib import Path

import typer

from al.config import (
    base_url_option,
    handle_connection_error,
    handle_timeout_error,
    httpx_client,
)

app = typer.Typer()


@app.command("evaluate")
def evaluate(
    file: Path | None = typer.Option(
        None,
        "--file",
        help="Path to Facts JSON file. Reads from stdin if not provided.",
    ),
    base_url: str = base_url_option(),
) -> None:
    """Evaluate a policy decision against a Facts JSON payload."""
    import httpx

    if file is not None:
        try:
            raw = file.read_text()
        except OSError as exc:
            typer.echo(f"Cannot read file: {exc}", err=True)
            raise typer.Exit(1)
    else:
        raw = sys.stdin.read()

    if not raw.strip():
        typer.echo(
            "No input provided. Supply --file or pipe Facts JSON via stdin.", err=True
        )
        raise typer.Exit(1)

    try:
        body = json.loads(raw)
    except json.JSONDecodeError as exc:
        typer.echo(f"Invalid JSON: {exc}", err=True)
        raise typer.Exit(1)

    url = f"{base_url.rstrip('/')}/api/v0/policy/evaluate"
    try:
        with httpx_client() as client:
            response = client.post(url, json=body)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as err:
                if err.response.status_code == 422:
                    typer.echo(f"Validation error: {err.response.text}", err=True)
                else:
                    typer.echo(f"API error: {err.response.text}", err=True)
                raise typer.Exit(1)
    except httpx.ConnectError:
        handle_connection_error(base_url)
    except httpx.TimeoutException:
        handle_timeout_error(base_url)

    typer.echo(json.dumps(response.json(), indent=2, default=str))
