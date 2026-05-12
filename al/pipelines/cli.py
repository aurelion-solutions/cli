"""Pipeline inspection subcommands for al CLI."""

from __future__ import annotations

import enum
import json
import uuid
from typing import Any, Callable, NoReturn

import httpx
import typer
from al.config import (
    base_url_option,
    handle_connection_error,
    handle_timeout_error,
    httpx_client,
)

app = typer.Typer(help="Inspect pipelines and pipeline runs.")
runs_app = typer.Typer(help="Inspect pipeline runs.")
app.add_typer(runs_app, name="runs")


class OutputFormat(str, enum.Enum):
    text = "text"
    json = "json"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _print(
    payload: Any, fmt: OutputFormat, text_renderer: Callable[[Any], None]
) -> None:
    """Print payload either as JSON or via the supplied text renderer."""
    if fmt == OutputFormat.json:
        typer.echo(json.dumps(payload, indent=2, default=str))
    else:
        text_renderer(payload)


def _handle_http_error(
    err: httpx.HTTPStatusError,
    *,
    not_found_msg: str | None = None,
) -> NoReturn:
    """Translate HTTPStatusError to a user-facing message and exit 1."""
    if err.response.status_code == 404 and not_found_msg is not None:
        typer.echo(not_found_msg, err=True)
    else:
        typer.echo(
            f"API error {err.response.status_code}: {err.response.text}",
            err=True,
        )
    raise typer.Exit(1)


def _get(
    base_url: str,
    path: str,
    params: list[tuple[str, str]] | dict[str, str] | None = None,
) -> httpx.Response:
    """Perform a GET request with shared error handling for connection/timeout."""
    url = f"{base_url.rstrip('/')}{path}"
    try:
        with httpx_client() as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response
    except httpx.ConnectError:
        handle_connection_error(base_url)
    except httpx.TimeoutException:
        handle_timeout_error(base_url)


def _post(base_url: str, path: str, body: dict[str, Any]) -> httpx.Response:
    """Perform a POST request with shared error handling for connection/timeout."""
    url = f"{base_url.rstrip('/')}{path}"
    try:
        with httpx_client() as client:
            response = client.post(url, json=body)
            response.raise_for_status()
            return response
    except httpx.ConnectError:
        handle_connection_error(base_url)
    except httpx.TimeoutException:
        handle_timeout_error(base_url)


# ---------------------------------------------------------------------------
# Text renderers
# ---------------------------------------------------------------------------


def _render_pipelines_list(items: list[dict[str, Any]]) -> None:
    if not items:
        typer.echo("No pipelines loaded.")
        return
    for p in items:
        name = p.get("name", "")
        version = p.get("version", "")
        step_count = p.get("step_count", 0)
        triggers = p.get("triggers", [])
        typer.echo(
            f"{name:30}  v{version}  steps={step_count}  triggers={len(triggers)}"
        )


def _render_pipeline_detail(detail: dict[str, Any]) -> None:
    typer.echo(f"name:          {detail.get('name')}")
    typer.echo(f"version:       {detail.get('version')}")
    typer.echo(f"schema_version:{detail.get('schema_version')}")
    typer.echo(f"content_hash:  {detail.get('content_hash')}")
    typer.echo(f"source_path:   {detail.get('source_path')}")
    typer.echo(f"description:   {detail.get('description')}")

    triggers = detail.get("triggers", [])
    if triggers:
        typer.echo("triggers:")
        for t in triggers:
            kind = t.get("type", "")
            extra = {k: v for k, v in t.items() if k != "type"}
            typer.echo(f"  {kind}  {extra}")

    steps = detail.get("steps", [])
    if steps:
        typer.echo("steps:")
        for s in steps:
            step_id = s.get("id", "")
            engine = s.get("engine", "")
            action = s.get("action", "")
            cond_if = s.get("if", "")
            cond_when = s.get("when", "")
            cond_str = f"  if={cond_if}" if cond_if else ""
            cond_str += f"  when={cond_when}" if cond_when else ""
            typer.echo(f"  {step_id}  {engine}.{action}{cond_str}")


def _render_runs_list(items: list[dict[str, Any]]) -> None:
    if not items:
        typer.echo("No pipeline runs found.")
        return
    for r in items:
        typer.echo(
            f"{r.get('id')}  {r.get('pipeline_name')}  "
            f"v{r.get('pipeline_version')}  {r.get('status')}  "
            f"started={r.get('started_at')}  finished={r.get('finished_at')}"
        )


def _render_pipeline_run_created(payload: dict[str, Any]) -> None:
    typer.echo(f"pipeline_run_id={payload.get('pipeline_run_id')}")
    typer.echo(f"status={payload.get('status')}")
    typer.echo(f"version={payload.get('pipeline_version')}")
    typer.echo(f"created={payload.get('created')}")


def _render_cancel_result(payload: dict[str, Any]) -> None:
    typer.echo(f"run_id={payload.get('run_id')}")
    typer.echo(f"status={payload.get('status')}")


def _render_retry_result(payload: dict[str, Any]) -> None:
    typer.echo(f"run_id={payload.get('run_id')}")
    typer.echo(f"retry_of_run_id={payload.get('retry_of_run_id')}")
    typer.echo(f"status={payload.get('status')}")
    typer.echo(f"pipeline={payload.get('pipeline_name')}")
    typer.echo(f"version={payload.get('pipeline_version')}")


def _render_run_detail(detail: dict[str, Any]) -> None:
    typer.echo(f"id:             {detail.get('id')}")
    typer.echo(f"pipeline:       {detail.get('pipeline_name')}")
    typer.echo(f"version:        {detail.get('pipeline_version')}")
    typer.echo(f"status:         {detail.get('status')}")
    typer.echo(f"trigger_source: {detail.get('trigger_source')}")
    typer.echo(f"current_step:   {detail.get('current_step')}")
    typer.echo(f"started_at:     {detail.get('started_at')}")
    typer.echo(f"finished_at:    {detail.get('finished_at')}")
    if detail.get("error"):
        typer.echo(f"error:          {detail.get('error')}")

    steps = detail.get("steps", [])
    if steps:
        typer.echo("steps:")
        for s in steps:
            typer.echo(
                f"  {s.get('step_name')}  attempt={s.get('attempt')}  "
                f"{s.get('status')}  "
                f"started={s.get('started_at')}  finished={s.get('finished_at')}"
            )


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command("list")
def pipelines_list(
    fmt: OutputFormat = typer.Option(
        OutputFormat.text, "--format", help="Output format"
    ),
    base_url: str = base_url_option(),
) -> None:
    """List all loaded pipeline definitions."""
    try:
        response = _get(base_url, "/api/v0/pipelines")
    except httpx.HTTPStatusError as err:
        _handle_http_error(err)

    payload = response.json()
    _print(payload, fmt, _render_pipelines_list)


@app.command("show")
def pipelines_show(
    name: str = typer.Argument(..., help="Pipeline name"),
    fmt: OutputFormat = typer.Option(
        OutputFormat.text, "--format", help="Output format"
    ),
    base_url: str = base_url_option(),
) -> None:
    """Show full details for a single pipeline definition."""
    try:
        response = _get(base_url, f"/api/v0/pipelines/{name}")
    except httpx.HTTPStatusError as err:
        _handle_http_error(err, not_found_msg=f"Pipeline {name!r} not loaded")

    payload = response.json()
    _print(payload, fmt, _render_pipeline_detail)


@runs_app.command("list")
def runs_list(
    pipeline: str | None = typer.Option(
        None, "--pipeline", help="Filter by pipeline name"
    ),
    status: list[str] | None = typer.Option(
        None, "--status", help="Filter by status (repeatable)"
    ),
    limit: int = typer.Option(50, "--limit", help="Maximum number of results"),
    offset: int = typer.Option(0, "--offset", help="Result offset for pagination"),
    fmt: OutputFormat = typer.Option(
        OutputFormat.text, "--format", help="Output format"
    ),
    base_url: str = base_url_option(),
) -> None:
    """List pipeline runs with optional filters."""
    params: list[tuple[str, str]] = [
        ("limit", str(limit)),
        ("offset", str(offset)),
    ]
    if pipeline is not None:
        params.append(("pipeline_name", pipeline))
    if status:
        params.extend([("status", v) for v in status])

    try:
        response = _get(base_url, "/api/v0/pipeline-runs", params=params)
    except httpx.HTTPStatusError as err:
        _handle_http_error(err)

    payload = response.json()
    _print(payload, fmt, _render_runs_list)


@app.command("run")
def pipelines_run(
    pipeline_name: str = typer.Argument(..., help="Pipeline name"),
    args: str = typer.Option("{}", "--args", help="Pipeline args as JSON object"),
    version: int | None = typer.Option(
        None, "--version", help="Pipeline version (omitted when not supplied)"
    ),
    fmt: OutputFormat = typer.Option(
        OutputFormat.text, "--format", help="Output format"
    ),
    base_url: str = base_url_option(),
) -> None:
    """Trigger a new pipeline run via POST /api/v0/pipeline-runs."""
    try:
        parsed_args = json.loads(args)
    except json.JSONDecodeError as exc:
        typer.echo(f"Invalid --args JSON: {exc}", err=True)
        raise typer.Exit(2)

    if not isinstance(parsed_args, dict):
        typer.echo("Invalid --args JSON: must be a JSON object (dict)", err=True)
        raise typer.Exit(2)

    body: dict[str, Any] = {"pipeline_name": pipeline_name, "args": parsed_args}
    if version is not None:
        body["pipeline_version"] = version

    try:
        response = _post(base_url, "/api/v0/pipeline-runs", body)
    except httpx.HTTPStatusError as err:
        status_code = err.response.status_code
        if status_code == 404:
            typer.echo(f"Pipeline {pipeline_name!r} not loaded", err=True)
            raise typer.Exit(1)
        if status_code == 422:
            try:
                detail = err.response.json().get("detail")
            except (ValueError, json.JSONDecodeError):
                detail = None
            if detail is not None:
                typer.echo(f"Invalid args: {detail}", err=True)
                raise typer.Exit(1)
        _handle_http_error(err)

    payload = response.json()
    _print(payload, fmt, _render_pipeline_run_created)


@runs_app.command("cancel")
def runs_cancel(
    run_id: uuid.UUID = typer.Argument(..., help="Pipeline run UUID"),
    fmt: OutputFormat = typer.Option(
        OutputFormat.text, "--format", help="Output format"
    ),
    base_url: str = base_url_option(),
) -> None:
    """Cancel a pipeline run via POST /api/v0/pipeline-runs/{run_id}/cancel."""
    try:
        response = _post(base_url, f"/api/v0/pipeline-runs/{run_id}/cancel", {})
    except httpx.HTTPStatusError as err:
        status_code = err.response.status_code
        if status_code == 404:
            typer.echo("Pipeline run not found", err=True)
            raise typer.Exit(1)
        if status_code == 409:
            try:
                detail = err.response.json().get("detail", err.response.text)
            except (ValueError, json.JSONDecodeError):
                detail = err.response.text
            typer.echo(detail, err=True)
            raise typer.Exit(1)
        _handle_http_error(err)

    payload = response.json()
    _print(payload, fmt, _render_cancel_result)


@runs_app.command("retry")
def runs_retry(
    run_id: uuid.UUID = typer.Argument(..., help="Pipeline run UUID"),
    fmt: OutputFormat = typer.Option(
        OutputFormat.text, "--format", help="Output format"
    ),
    base_url: str = base_url_option(),
) -> None:
    """Retry a pipeline run via POST /api/v0/pipeline-runs/{run_id}/retry."""
    try:
        response = _post(base_url, f"/api/v0/pipeline-runs/{run_id}/retry", {})
    except httpx.HTTPStatusError as err:
        status_code = err.response.status_code
        if status_code == 404:
            typer.echo("Pipeline run not found", err=True)
            raise typer.Exit(1)
        if status_code == 409:
            try:
                detail = err.response.json().get("detail", err.response.text)
            except (ValueError, json.JSONDecodeError):
                detail = err.response.text
            typer.echo(detail, err=True)
            raise typer.Exit(1)
        _handle_http_error(err)

    payload = response.json()
    _print(payload, fmt, _render_retry_result)


@runs_app.command("get")
def runs_get(
    run_id: uuid.UUID = typer.Argument(..., help="Pipeline run UUID"),
    fmt: OutputFormat = typer.Option(
        OutputFormat.text, "--format", help="Output format"
    ),
    base_url: str = base_url_option(),
) -> None:
    """Get details for a single pipeline run."""
    try:
        response = _get(base_url, f"/api/v0/pipeline-runs/{run_id}")
    except httpx.HTTPStatusError as err:
        _handle_http_error(err, not_found_msg="Pipeline run not found")

    payload = response.json()
    _print(payload, fmt, _render_run_detail)
