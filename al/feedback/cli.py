"""Feedback subcommands."""

import json
from pathlib import Path

import typer

from al.config import (
    base_url_option,
    handle_connection_error,
    handle_timeout_error,
    httpx_client,
)

app = typer.Typer()


@app.command("post")
def post(
    kind: str = typer.Option(
        ...,
        "--kind",
        help=(
            "Feedback kind: accepted_risk | false_positive | needs_mapping_fix | "
            "needs_rule_fix | needs_mitigation"
        ),
    ),
    message: str = typer.Option(
        ...,
        "--message",
        help="Feedback message (required, min length 1)",
    ),
    rule: int | None = typer.Option(
        None,
        "--rule",
        help="SoD rule ID (at least one of --rule, --mapping, --finding required)",
    ),
    mapping: int | None = typer.Option(
        None,
        "--mapping",
        help="Capability mapping ID (at least one of --rule, --mapping, --finding required)",
    ),
    finding: int | None = typer.Option(
        None,
        "--finding",
        help="Finding ID (at least one of --rule, --mapping, --finding required)",
    ),
    subject: str | None = typer.Option(
        None,
        "--subject",
        help="Subject UUID (optional context)",
    ),
    payload_file: Path | None = typer.Option(
        None,
        "--payload-file",
        help="Path to a JSON file to include as structured payload",
    ),
    created_by: str | None = typer.Option(
        None,
        "--created-by",
        help="Actor identifier recorded on the feedback",
    ),
    base_url: str = base_url_option(),
) -> None:
    """Post structured feedback against a finding, rule, or capability mapping."""
    import httpx

    # Client-side guard: at least one target FK required
    if rule is None and mapping is None and finding is None:
        typer.echo(
            "At least one of --rule, --mapping, or --finding must be provided.",
            err=True,
        )
        raise typer.Exit(2)

    payload_data: object = None
    if payload_file is not None:
        try:
            raw = payload_file.read_text()
        except OSError as exc:
            typer.echo(f"Cannot read payload file: {exc}", err=True)
            raise typer.Exit(2)
        try:
            payload_data = json.loads(raw)
        except json.JSONDecodeError as exc:
            typer.echo(f"Invalid JSON in payload file: {exc}", err=True)
            raise typer.Exit(2)

    body: dict[str, object] = {"kind": kind, "message": message}
    if rule is not None:
        body["rule_id"] = rule
    if mapping is not None:
        body["capability_mapping_id"] = mapping
    if finding is not None:
        body["finding_id"] = finding
    if subject is not None:
        body["subject_id"] = subject
    if payload_data is not None:
        body["payload"] = payload_data
    if created_by is not None:
        body["created_by"] = created_by

    url = f"{base_url.rstrip('/')}/api/v0/feedbacks"
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
