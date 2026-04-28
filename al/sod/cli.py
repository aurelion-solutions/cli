"""SoD (Segregation of Duties) subcommands."""

import json
import sys
import uuid
from pathlib import Path

import typer

from al.config import (
    base_url_option,
    handle_connection_error,
    handle_timeout_error,
    httpx_client,
)

app = typer.Typer()


@app.command("apply")
def apply(
    file: Path = typer.Argument(
        ..., help="Path to YAML or JSON file with SoD rule definitions"
    ),
    created_by: str | None = typer.Option(
        None, "--created-by", help="Actor identifier recorded on created rules"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Print payload without sending"
    ),
    base_url: str = base_url_option(),
) -> None:
    """Apply SoD rules from a config file (config-as-code, idempotent).

    YAML example:

    \b
    rules:
      - code: SOD_AP_001
        name: Vendor Creation + Payment Approval
        severity: critical
        scope_mode: global
        conditions:
          - name: Creates vendors
            min_count: 1
            capabilities: [create_vendor]
          - name: Approves payments
            min_count: 1
            capabilities: [approve_payment]
    """
    import httpx

    try:
        raw = file.read_text()
    except OSError as exc:
        typer.echo(f"Cannot read file: {exc}", err=True)
        raise typer.Exit(1)

    suffix = file.suffix.lower()
    if suffix in (".yaml", ".yml"):
        try:
            import yaml  # type: ignore[import]
        except ImportError:
            typer.echo("PyYAML not installed. Run: uv add pyyaml", err=True)
            raise typer.Exit(1)
        try:
            parsed = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            typer.echo(f"Invalid YAML: {exc}", err=True)
            raise typer.Exit(2)
    else:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            typer.echo(f"Invalid JSON: {exc}", err=True)
            raise typer.Exit(2)

    if not isinstance(parsed, dict) or "rules" not in parsed:
        typer.echo('File must contain a top-level "rules" key.', err=True)
        raise typer.Exit(2)

    body: dict[str, object] = {"rules": parsed["rules"]}
    if created_by is not None:
        body["created_by"] = created_by

    if dry_run:
        typer.echo(json.dumps(body, indent=2, default=str))
        return

    url = f"{base_url.rstrip('/')}/api/v0/sod-rules/apply"
    try:
        with httpx_client() as client:
            response = client.post(url, json=body)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as err:
                typer.echo(
                    f"API error ({err.response.status_code}): {err.response.text}",
                    err=True,
                )
                raise typer.Exit(1)
    except httpx.ConnectError:
        handle_connection_error(base_url)
    except httpx.TimeoutException:
        handle_timeout_error(base_url)

    result = response.json()
    typer.echo(
        f"rules: +{result.get('rules_created', 0)} updated={result.get('rules_updated', 0)} "
        f"unchanged={result.get('rules_unchanged', 0)}"
    )
    typer.echo(
        f"conditions: +{result.get('conditions_created', 0)} -{result.get('conditions_deleted', 0)}"
    )
    if result.get("unknown_capabilities"):
        typer.echo(
            f"ERROR: unknown capabilities: {result['unknown_capabilities']}", err=True
        )
        raise typer.Exit(1)


@app.command("evaluate")
def evaluate(
    subject_id: str = typer.Argument(..., help="Subject ID (UUID)"),
    at: str | None = typer.Option(
        None,
        "--at",
        help="Point-in-time ISO 8601 timestamp (omit to use server default of now(UTC))",
    ),
    base_url: str = base_url_option(),
) -> None:
    """Evaluate SoD violations for a subject at a given point in time."""
    import httpx

    body: dict[str, object] = {"subject_id": subject_id}
    if at is not None:
        body["at"] = at

    url = f"{base_url.rstrip('/')}/api/v0/sod/evaluate"
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


def _parse_override(raw: str) -> dict[str, object]:
    """Parse a colon-separated 4-tuple into a CapabilityGrantOverride dict.

    Format: CAP_ID:SCOPE_KEY_ID:SCOPE_VALUE_OR_NULL:APP_UUID
    - CAP_ID: int
    - SCOPE_KEY_ID: int
    - SCOPE_VALUE_OR_NULL: literal "null" (case-insensitive) -> JSON null; otherwise str
    - APP_UUID: UUID (validated for early failure)
    """
    parts = raw.split(":", 3)
    if len(parts) != 4:
        raise ValueError(
            f"expected 4 colon-separated fields, got {len(parts)}: {raw!r}"
        )

    cap_id_str, scope_key_id_str, scope_value_str, app_uuid_str = parts

    try:
        capability_id = int(cap_id_str)
    except ValueError:
        raise ValueError(f"capability_id must be an integer, got {cap_id_str!r}")

    try:
        scope_key_id = int(scope_key_id_str)
    except ValueError:
        raise ValueError(f"scope_key_id must be an integer, got {scope_key_id_str!r}")

    scope_value: str | None = (
        None if scope_value_str.lower() == "null" else scope_value_str
    )

    try:
        application_id = str(uuid.UUID(app_uuid_str))
    except ValueError:
        raise ValueError(f"application_id must be a valid UUID, got {app_uuid_str!r}")

    return {
        "capability_id": capability_id,
        "scope_key_id": scope_key_id,
        "scope_value": scope_value,
        "application_id": application_id,
    }


@app.command("what-if")
def what_if(
    subject_id: str = typer.Argument(..., help="Subject ID (UUID)"),
    override: list[str] = typer.Option(
        default_factory=list,
        help=(
            "Capability override (repeatable). "
            "Format: CAP_ID:SCOPE_KEY_ID:SCOPE_VALUE_OR_NULL:APP_UUID. "
            "Use literal 'null' for scope_value to represent no scope. "
            "Empty list is allowed (degenerates to /sod/evaluate)."
        ),
    ),
    at: str | None = typer.Option(
        None,
        "--at",
        help="Point-in-time ISO 8601 timestamp (omit to use server default of now(UTC))",
    ),
    base_url: str = base_url_option(),
) -> None:
    """Evaluate SoD violations for a subject with synthetic capability overrides (what-if)."""
    import httpx

    capability_overrides: list[dict[str, object]] = []
    for raw in override:
        try:
            capability_overrides.append(_parse_override(raw))
        except ValueError as exc:
            typer.echo(f"Invalid --override: {exc}", err=True)
            raise typer.Exit(2)

    body: dict[str, object] = {
        "subject_id": subject_id,
        "capability_overrides": capability_overrides,
    }
    if at is not None:
        body["at"] = at

    url = f"{base_url.rstrip('/')}/api/v0/sod/what-if"
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


@app.command("resolve-capabilities")
def resolve_capabilities(
    file: Path | None = typer.Option(
        None,
        "--file",
        help="Path to JSON file containing sources. Reads from stdin if not provided.",
    ),
    base_url: str = base_url_option(),
) -> None:
    """Resolve EffectiveGrant sources back to capability slugs.

    Input JSON must be either:
    - an object with a "sources" key: {"sources": [...]}
    - a top-level list [...] — wrapped automatically as {"sources": [...]}
    """
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
        typer.echo("No input provided. Supply --file or pipe JSON via stdin.", err=True)
        raise typer.Exit(2)

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        typer.echo(f"Invalid JSON: {exc}", err=True)
        raise typer.Exit(2)

    if isinstance(parsed, list):
        body = {"sources": parsed}
    elif isinstance(parsed, dict) and "sources" in parsed:
        body = parsed
    else:
        typer.echo(
            'Invalid input: expected an object with "sources" or a top-level list.',
            err=True,
        )
        raise typer.Exit(2)

    url = f"{base_url.rstrip('/')}/api/v0/sod/resolve-capabilities"
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
