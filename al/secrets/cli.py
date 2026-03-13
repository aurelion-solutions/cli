"""Secrets subcommand for secret operations."""

import json
from urllib.parse import quote

import typer

from al.config import (
    base_url_option,
    handle_connection_error,
    handle_timeout_error,
    httpx_client,
)

app = typer.Typer()
provider_app = typer.Typer()
app.add_typer(provider_app, name="provider")


@app.command("list")
def list_cmd(
    provider: str = typer.Option(None, "--provider", help="Filter by provider"),
    namespace: str = typer.Option(None, "--namespace", help="Filter by namespace"),
    base_url: str = base_url_option(),
):
    """List secrets (metadata only, no values)."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/secrets"
    params = {}
    if provider:
        params["provider"] = provider
    if namespace:
        params["namespace"] = namespace
    try:
        with httpx_client() as client:
            response = client.get(url, params=params)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as err:
                typer.echo(f"API error: {err.response.text}", err=True)
                raise typer.Exit(1)
    except httpx.ConnectError:
        handle_connection_error(base_url)
    except httpx.TimeoutException:
        handle_timeout_error(base_url)
    secrets = response.json()
    if not secrets:
        typer.echo("No secrets")
        return
    for s in secrets:
        typer.echo(f"{s['key']}  {s['provider']}  {s['namespace']}")


@app.command("create")
def create(
    key: str = typer.Option(
        ..., "--key", help="Secret key (path-like: segment/segment)"
    ),
    provider: str = typer.Option(..., "--provider", help="Provider (e.g. file, vault)"),
    namespace: str = typer.Option(..., "--namespace", help="Namespace (e.g. default)"),
    value: str = typer.Option(..., "--value", help="Secret value"),
    base_url: str = base_url_option(),
):
    """Create a secret."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/secrets"
    payload = {"key": key, "provider": provider, "namespace": namespace, "value": value}
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
    typer.echo("Secret created")


@app.command("get")
def get(
    key: str = typer.Option(..., "--key", help="Secret key"),
    provider: str = typer.Option(..., "--provider", help="Provider"),
    namespace: str = typer.Option(..., "--namespace", help="Namespace"),
    base_url: str = base_url_option(),
):
    """Get a secret value."""
    import httpx

    encoded_key = quote(key, safe="/")
    url = f"{base_url.rstrip('/')}/api/v0/secrets/{provider}/{encoded_key}"
    params = {"namespace": namespace}
    try:
        with httpx_client() as client:
            response = client.get(url, params=params)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as err:
                typer.echo(f"API error: {err.response.text}", err=True)
                raise typer.Exit(1)
    except httpx.ConnectError:
        handle_connection_error(base_url)
    except httpx.TimeoutException:
        handle_timeout_error(base_url)
    typer.echo(response.text)


@app.command("delete")
def delete(
    key: str = typer.Option(..., "--key", help="Secret key"),
    provider: str = typer.Option(..., "--provider", help="Provider"),
    namespace: str = typer.Option(..., "--namespace", help="Namespace"),
    base_url: str = base_url_option(),
):
    """Delete a secret."""
    import httpx

    encoded_key = quote(key, safe="/")
    url = f"{base_url.rstrip('/')}/api/v0/secrets/{provider}/{encoded_key}"
    params = {"namespace": namespace}
    try:
        with httpx_client() as client:
            response = client.delete(url, params=params)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as err:
                typer.echo(f"API error: {err.response.text}", err=True)
                raise typer.Exit(1)
    except httpx.ConnectError:
        handle_connection_error(base_url)
    except httpx.TimeoutException:
        handle_timeout_error(base_url)
    typer.echo("Secret deleted")


# --- Provider commands ---


@provider_app.command("list")
def provider_list(
    base_url: str = base_url_option(),
) -> None:
    """List secret providers (built-in + custom)."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/secrets/providers"
    try:
        with httpx_client() as client:
            response = client.get(url)
            response.raise_for_status()
    except httpx.ConnectError:
        handle_connection_error(base_url)
    except httpx.TimeoutException:
        handle_timeout_error(base_url)
    except httpx.HTTPStatusError as err:
        typer.echo(f"API error: {err.response.text}", err=True)
        raise typer.Exit(1)
    providers = response.json()
    if not providers:
        typer.echo("No providers")
        return
    for p in providers:
        config_str = json.dumps(p["config"]) if p["config"] else "-"
        typer.echo(f"{p['name']}  {p['type']}  {config_str}")


@provider_app.command("create")
def provider_create(
    name: str = typer.Option(..., "--name", help="Provider name (alphanumeric, -_)"),
    type: str = typer.Option(..., "--type", help="Provider type (e.g. file)"),
    config: str = typer.Option(
        "{}", "--config", help='Config as JSON (e.g. {"path": "/path/to/secrets.json"})'
    ),
    base_url: str = base_url_option(),
) -> None:
    """Create a custom provider."""
    import httpx

    try:
        config_dict = json.loads(config) if config else {}
    except json.JSONDecodeError as err:
        typer.echo(f"Invalid --config JSON: {err}", err=True)
        raise typer.Exit(1)
    url = f"{base_url.rstrip('/')}/api/v0/secrets/providers"
    payload = {"name": name, "type": type, "config": config_dict}
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
    typer.echo(f"Created provider {result['name']} (type={result['type']})")


@provider_app.command("get")
def provider_get(
    name: str = typer.Option(..., "--name", help="Provider name"),
    base_url: str = base_url_option(),
) -> None:
    """Get a provider by name."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/secrets/providers/{name}"
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
    p = response.json()
    typer.echo(f"name: {p['name']}")
    typer.echo(f"type: {p['type']}")
    typer.echo(f"config: {json.dumps(p['config'])}")


@provider_app.command("delete")
def provider_delete(
    name: str = typer.Option(..., "--name", help="Provider name to delete"),
    base_url: str = base_url_option(),
) -> None:
    """Delete a custom provider."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/secrets/providers/{name}"
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
    typer.echo("Provider deleted")
