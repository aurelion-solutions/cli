"""Shared CLI configuration options."""

import os

import httpx
import typer

# Prevent indefinite hangs when the host is down, DNS stalls, or TCP connects but nothing responds.
DEFAULT_HTTP_TIMEOUT = httpx.Timeout(30.0, connect=5.0)


def httpx_client(**kwargs) -> httpx.Client:
    """``httpx.Client`` with sane defaults; extra kwargs are passed through (e.g. ``base_url``)."""
    return httpx.Client(**{"timeout": DEFAULT_HTTP_TIMEOUT, **kwargs})


def base_url_option():
    """Typer Option for API base URL."""
    return typer.Option(
        os.environ.get("AURELION_API_URL", "http://localhost:8000"),
        "--base-url",
        envvar="AURELION_API_URL",
        help="API base URL",
    )


def handle_connection_error(base_url: str) -> None:
    """Echo connection error and exit with code 1."""
    typer.echo(f"Connection refused. Is the API running at {base_url}?", err=True)
    raise typer.Exit(1)


def handle_timeout_error(base_url: str) -> None:
    """Echo timeout and exit with code 1."""
    typer.echo(
        f"Request timed out reaching {base_url}. Is the API running and reachable?",
        err=True,
    )
    raise typer.Exit(1)
