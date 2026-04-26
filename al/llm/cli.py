"""LLM subcommands: al llm profile *"""

import json

import typer

from al.config import (
    base_url_option,
    handle_connection_error,
    handle_timeout_error,
    httpx_client,
)

app = typer.Typer(help='LLM platform commands.')
profile_app = typer.Typer(help='Manage LLM execution profiles.')
app.add_typer(profile_app, name='profile')


def _parse_param_overrides(value: str | None) -> dict:
    """Parse a JSON string (or @path) into a dict.

    Supports:
    * ``'{"temperature": 0.5}'``   — inline JSON
    * ``'@/path/to/file.json'``    — read from file
    """
    if value is None:
        return {}
    if value.startswith('@'):
        path = value[1:]
        try:
            with open(path) as fh:
                return json.load(fh)
        except (OSError, json.JSONDecodeError) as err:
            typer.echo(f'Cannot read param-overrides from {path}: {err}', err=True)
            raise typer.Exit(1)
    try:
        return json.loads(value)
    except json.JSONDecodeError as err:
        typer.echo(f'Invalid --param-overrides JSON: {err}', err=True)
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# al llm profile list
# ---------------------------------------------------------------------------


@profile_app.command('list')
def profile_list(
    base_url: str = base_url_option(),
) -> None:
    """List all LLM execution profiles."""
    import httpx

    url = f'{base_url.rstrip("/")}/api/v0/llm/execution-profiles'
    try:
        with httpx_client() as client:
            response = client.get(url)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as err:
                typer.echo(f'API error: {err.response.text}', err=True)
                raise typer.Exit(1)
    except httpx.ConnectError:
        handle_connection_error(base_url)
    except httpx.TimeoutException:
        handle_timeout_error(base_url)
    profiles = response.json()
    if not profiles:
        typer.echo('No execution profiles')
        return
    for p in profiles:
        typer.echo(f"{p['id']}  {p['name']}  model={p['model_id']}")


# ---------------------------------------------------------------------------
# al llm profile show <id>
# ---------------------------------------------------------------------------


@profile_app.command('show')
def profile_show(
    profile_id: str = typer.Argument(..., help='Profile UUID'),
    base_url: str = base_url_option(),
) -> None:
    """Show a single LLM execution profile as JSON."""
    import httpx

    url = f'{base_url.rstrip("/")}/api/v0/llm/execution-profiles/{profile_id}'
    try:
        with httpx_client() as client:
            response = client.get(url)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as err:
                typer.echo(f'API error: {err.response.text}', err=True)
                raise typer.Exit(1)
    except httpx.ConnectError:
        handle_connection_error(base_url)
    except httpx.TimeoutException:
        handle_timeout_error(base_url)
    typer.echo(json.dumps(response.json(), indent=2))


# ---------------------------------------------------------------------------
# al llm profile create
# ---------------------------------------------------------------------------


@profile_app.command('create')
def profile_create(
    name: str = typer.Option(..., '--name', help='Profile name'),
    model_id: str = typer.Option(..., '--model-id', help='LLMModel UUID'),
    param_overrides: str | None = typer.Option(
        None,
        '--param-overrides',
        help='JSON dict or @path to JSON file',
    ),
    base_url: str = base_url_option(),
) -> None:
    """Create a new LLM execution profile."""
    import httpx

    overrides = _parse_param_overrides(param_overrides)
    payload = {'name': name, 'model_id': model_id, 'param_overrides': overrides}
    url = f'{base_url.rstrip("/")}/api/v0/llm/execution-profiles'
    try:
        with httpx_client() as client:
            response = client.post(url, json=payload)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as err:
                typer.echo(f'API error: {err.response.text}', err=True)
                raise typer.Exit(1)
    except httpx.ConnectError:
        handle_connection_error(base_url)
    except httpx.TimeoutException:
        handle_timeout_error(base_url)
    typer.echo(json.dumps(response.json(), indent=2))


# ---------------------------------------------------------------------------
# al llm profile update <id>
# ---------------------------------------------------------------------------


@profile_app.command('update')
def profile_update(
    profile_id: str = typer.Argument(..., help='Profile UUID'),
    name: str | None = typer.Option(None, '--name', help='New profile name'),
    param_overrides: str | None = typer.Option(
        None,
        '--param-overrides',
        help='JSON dict or @path to JSON file',
    ),
    base_url: str = base_url_option(),
) -> None:
    """Update an LLM execution profile (PATCH — only supplied fields are changed)."""
    import httpx

    payload: dict = {}
    if name is not None:
        payload['name'] = name
    if param_overrides is not None:
        payload['param_overrides'] = _parse_param_overrides(param_overrides)

    if not payload:
        typer.echo('Nothing to update — provide --name or --param-overrides.', err=True)
        raise typer.Exit(1)

    url = f'{base_url.rstrip("/")}/api/v0/llm/execution-profiles/{profile_id}'
    try:
        with httpx_client() as client:
            response = client.patch(url, json=payload)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as err:
                typer.echo(f'API error: {err.response.text}', err=True)
                raise typer.Exit(1)
    except httpx.ConnectError:
        handle_connection_error(base_url)
    except httpx.TimeoutException:
        handle_timeout_error(base_url)
    typer.echo(json.dumps(response.json(), indent=2))


# ---------------------------------------------------------------------------
# al llm profile delete <id>
# ---------------------------------------------------------------------------


@profile_app.command('delete')
def profile_delete(
    profile_id: str = typer.Argument(..., help='Profile UUID'),
    yes: bool = typer.Option(False, '--yes', help='Confirm deletion without prompt'),
    base_url: str = base_url_option(),
) -> None:
    """Delete an LLM execution profile."""
    import httpx

    if not yes:
        typer.echo('Pass --yes to confirm deletion.', err=True)
        raise typer.Exit(1)

    url = f'{base_url.rstrip("/")}/api/v0/llm/execution-profiles/{profile_id}'
    try:
        with httpx_client() as client:
            response = client.delete(url)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as err:
                typer.echo(f'API error: {err.response.text}', err=True)
                raise typer.Exit(1)
    except httpx.ConnectError:
        handle_connection_error(base_url)
    except httpx.TimeoutException:
        handle_timeout_error(base_url)
    typer.echo('Profile deleted')
