"""Inventory subcommands (accounts, ...)."""

import json

import typer

from al.config import (
    base_url_option,
    handle_connection_error,
    handle_timeout_error,
    httpx_client,
)

app = typer.Typer()
accounts = typer.Typer()
app.add_typer(accounts, name="accounts")
resources = typer.Typer()
app.add_typer(resources, name="resources")
artifacts = typer.Typer()
app.add_typer(artifacts, name="artifacts")
access_facts = typer.Typer()
app.add_typer(access_facts, name="access-facts")
artifact_bindings = typer.Typer()
app.add_typer(artifact_bindings, name="artifact-bindings")
initiatives = typer.Typer()
app.add_typer(initiatives, name="initiatives")
ownership = typer.Typer()
app.add_typer(ownership, name="ownership-assignments")
usage_facts = typer.Typer()
app.add_typer(usage_facts, name="usage-facts")
threat_facts = typer.Typer()
app.add_typer(threat_facts, name="threat-facts")
customers = typer.Typer()
app.add_typer(customers, name="customers")
subjects = typer.Typer()
app.add_typer(subjects, name="subjects")
# subject (singular) is registered as @app.command("subject") below


@accounts.command("list")
def list_accounts(
    application: str | None = typer.Option(
        None, "--application", help="Application ID (UUID)"
    ),
    status: str | None = typer.Option(
        None, "--status", help="Filter by account status"
    ),
    subject: str | None = typer.Option(
        None, "--subject", help="Filter by subject ID (UUID)"
    ),
    base_url: str = base_url_option(),
) -> None:
    """List accounts with optional filters."""
    import httpx

    params: dict[str, str] = {}
    if application is not None:
        params["application_id"] = application
    if status is not None:
        params["status"] = status
    if subject is not None:
        params["subject_id"] = subject
    url = f"{base_url.rstrip('/')}/api/v0/accounts"
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
    typer.echo(json.dumps(response.json(), indent=2, default=str))


@accounts.command("get")
def get_account(
    account_id: str = typer.Argument(..., help="Account ID (UUID)"),
    base_url: str = base_url_option(),
) -> None:
    """Get account by id."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/accounts/{account_id}"
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


@accounts.command("update")
def update_account(
    account_id: str = typer.Argument(..., help="Account ID (UUID)"),
    status: str | None = typer.Option(None, "--status", help="New account status"),
    subject: str | None = typer.Option(
        None, "--subject", help="Subject ID (UUID) to bind"
    ),
    base_url: str = base_url_option(),
) -> None:
    """Update account status and/or subject binding."""
    import httpx

    if status is None and subject is None:
        typer.echo("Nothing to update. Provide --status or --subject.", err=True)
        raise typer.Exit(1)
    payload: dict[str, str] = {}
    if status is not None:
        payload["status"] = status
    if subject is not None:
        payload["subject_id"] = subject
    url = f"{base_url.rstrip('/')}/api/v0/accounts/{account_id}"
    try:
        with httpx_client() as client:
            response = client.patch(url, json=payload)
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


# ---------------------------------------------------------------------------
# Resources sub-commands
# ---------------------------------------------------------------------------


@resources.command("list")
def list_resources(
    application: str | None = typer.Option(
        None, "--application", help="Application ID (UUID)"
    ),
    kind: str | None = typer.Option(None, "--kind", help="Filter by resource kind"),
    privilege_level: str | None = typer.Option(
        None, "--privilege-level", help="Filter by privilege level"
    ),
    environment: str | None = typer.Option(
        None, "--environment", help="Filter by environment"
    ),
    data_sensitivity: str | None = typer.Option(
        None, "--data-sensitivity", help="Filter by data sensitivity"
    ),
    base_url: str = base_url_option(),
) -> None:
    """List resources with optional filters."""
    import httpx

    params: dict[str, str] = {}
    if application is not None:
        params["application_id"] = application
    if kind is not None:
        params["kind"] = kind
    if privilege_level is not None:
        params["privilege_level"] = privilege_level
    if environment is not None:
        params["environment"] = environment
    if data_sensitivity is not None:
        params["data_sensitivity"] = data_sensitivity
    url = f"{base_url.rstrip('/')}/api/v0/resources"
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
    typer.echo(json.dumps(response.json(), indent=2, default=str))


@resources.command("get")
def get_resource(
    resource_id: str = typer.Argument(..., help="Resource ID (UUID)"),
    base_url: str = base_url_option(),
) -> None:
    """Get resource by id."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/resources/{resource_id}"
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


@resources.command("create")
def create_resource(
    external_id: str = typer.Option(..., "--external-id", help="External ID"),
    application: str = typer.Option(..., "--application", help="Application ID (UUID)"),
    kind: str = typer.Option(..., "--kind", help="Resource kind"),
    parent: str | None = typer.Option(
        None, "--parent", help="Parent resource ID (UUID)"
    ),
    path: str | None = typer.Option(None, "--path", help="Resource path"),
    description: str | None = typer.Option(None, "--description", help="Description"),
    privilege_level: str | None = typer.Option(
        None, "--privilege-level", help="Privilege level"
    ),
    environment: str | None = typer.Option(None, "--environment", help="Environment"),
    data_sensitivity: str | None = typer.Option(
        None, "--data-sensitivity", help="Data sensitivity"
    ),
    base_url: str = base_url_option(),
) -> None:
    """Create a new resource."""
    import httpx

    payload: dict[str, object] = {
        "external_id": external_id,
        "application_id": application,
        "kind": kind,
    }
    if parent is not None:
        payload["parent_id"] = parent
    if path is not None:
        payload["path"] = path
    if description is not None:
        payload["description"] = description
    if privilege_level is not None:
        payload["privilege_level"] = privilege_level
    if environment is not None:
        payload["environment"] = environment
    if data_sensitivity is not None:
        payload["data_sensitivity"] = data_sensitivity
    url = f"{base_url.rstrip('/')}/api/v0/resources"
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
    typer.echo(json.dumps(response.json(), indent=2, default=str))


@resources.command("update")
def update_resource(
    resource_id: str = typer.Argument(..., help="Resource ID (UUID)"),
    kind: str | None = typer.Option(None, "--kind", help="New kind"),
    parent: str | None = typer.Option(None, "--parent", help="New parent ID (UUID)"),
    path: str | None = typer.Option(None, "--path", help="New path"),
    description: str | None = typer.Option(
        None, "--description", help="New description"
    ),
    privilege_level: str | None = typer.Option(
        None, "--privilege-level", help="New privilege level"
    ),
    environment: str | None = typer.Option(
        None, "--environment", help="New environment"
    ),
    data_sensitivity: str | None = typer.Option(
        None, "--data-sensitivity", help="New data sensitivity"
    ),
    base_url: str = base_url_option(),
) -> None:
    """Update a resource (partial update)."""
    import httpx

    payload: dict[str, object] = {}
    if kind is not None:
        payload["kind"] = kind
    if parent is not None:
        payload["parent_id"] = parent
    if path is not None:
        payload["path"] = path
    if description is not None:
        payload["description"] = description
    if privilege_level is not None:
        payload["privilege_level"] = privilege_level
    if environment is not None:
        payload["environment"] = environment
    if data_sensitivity is not None:
        payload["data_sensitivity"] = data_sensitivity
    if not payload:
        typer.echo(
            "Nothing to update. Provide at least one option (--kind, --parent, --path, "
            "--description, --privilege-level, --environment, --data-sensitivity).",
            err=True,
        )
        raise typer.Exit(1)
    url = f"{base_url.rstrip('/')}/api/v0/resources/{resource_id}"
    try:
        with httpx_client() as client:
            response = client.patch(url, json=payload)
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


@resources.command("attributes")
def list_resource_attributes(
    resource_id: str = typer.Argument(..., help="Resource ID (UUID)"),
    base_url: str = base_url_option(),
) -> None:
    """List attributes for a resource."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/resources/{resource_id}/attributes"
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


@resources.command("add-attribute")
def add_resource_attribute(
    resource_id: str = typer.Argument(..., help="Resource ID (UUID)"),
    key: str = typer.Option(..., "--key", help="Attribute key"),
    value: str = typer.Option(..., "--value", help="Attribute value"),
    base_url: str = base_url_option(),
) -> None:
    """Add an attribute to a resource."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/resources/{resource_id}/attributes"
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


@resources.command("remove-attribute")
def remove_resource_attribute(
    resource_id: str = typer.Argument(..., help="Resource ID (UUID)"),
    key: str = typer.Argument(..., help="Attribute key"),
    base_url: str = base_url_option(),
) -> None:
    """Remove an attribute from a resource."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/resources/{resource_id}/attributes/{key}"
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
    typer.echo("Attribute removed.")


# ---------------------------------------------------------------------------
# Artifacts sub-commands
# ---------------------------------------------------------------------------


@artifacts.command("list")
def list_artifacts(
    application: str | None = typer.Option(
        None, "--application", help="Application ID (UUID)"
    ),
    source_kind: str | None = typer.Option(
        None, "--source-kind", help="Filter by source kind"
    ),
    limit: int = typer.Option(50, "--limit", help="Maximum number of results"),
    base_url: str = base_url_option(),
) -> None:
    """List access artifacts with optional filters."""
    import httpx

    params: dict[str, str] = {}
    if application is not None:
        params["application_id"] = application
    if source_kind is not None:
        params["source_kind"] = source_kind
    params["limit"] = str(limit)
    url = f"{base_url.rstrip('/')}/api/v0/access-artifacts"
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
    typer.echo(json.dumps(response.json(), indent=2, default=str))


@artifacts.command("get")
def get_artifact(
    artifact_id: str = typer.Argument(..., help="Artifact ID (UUID)"),
    base_url: str = base_url_option(),
) -> None:
    """Get access artifact by id."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/access-artifacts/{artifact_id}"
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


# ---------------------------------------------------------------------------
# Access Facts sub-commands
# ---------------------------------------------------------------------------


@access_facts.command("list")
def list_access_facts(
    subject: str | None = typer.Option(None, "--subject", help="Subject ID (UUID)"),
    resource: str | None = typer.Option(None, "--resource", help="Resource ID (UUID)"),
    account: str | None = typer.Option(None, "--account", help="Account ID (UUID)"),
    action: str | None = typer.Option(None, "--action", help="Filter by action"),
    effect: str | None = typer.Option(
        None, "--effect", help="Filter by effect (allow|deny)"
    ),
    valid_at: str | None = typer.Option(
        None, "--valid-at", help="ISO datetime for validity window filter"
    ),
    limit: int = typer.Option(50, "--limit", help="Maximum number of results"),
    base_url: str = base_url_option(),
) -> None:
    """List access facts with optional filters."""
    import httpx

    params: dict[str, str] = {}
    if subject is not None:
        params["subject_id"] = subject
    if resource is not None:
        params["resource_id"] = resource
    if account is not None:
        params["account_id"] = account
    if action is not None:
        params["action"] = action
    if effect is not None:
        params["effect"] = effect
    if valid_at is not None:
        params["valid_at"] = valid_at
    params["limit"] = str(limit)
    url = f"{base_url.rstrip('/')}/api/v0/access-facts"
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
    typer.echo(json.dumps(response.json(), indent=2, default=str))


# ---------------------------------------------------------------------------
# Artifact Bindings sub-commands
# ---------------------------------------------------------------------------


@artifact_bindings.command("list")
def list_artifact_bindings(
    artifact: str | None = typer.Option(None, "--artifact", help="Artifact ID (UUID)"),
    access_fact: str | None = typer.Option(
        None, "--access-fact", help="Access Fact ID (UUID)"
    ),
    resource: str | None = typer.Option(None, "--resource", help="Resource ID (UUID)"),
    account: str | None = typer.Option(None, "--account", help="Account ID (UUID)"),
    limit: int = typer.Option(50, "--limit", help="Maximum number of results"),
    base_url: str = base_url_option(),
) -> None:
    """List artifact bindings with optional filters."""
    import httpx

    params: dict[str, str] = {}
    if artifact is not None:
        params["artifact_id"] = artifact
    if access_fact is not None:
        params["access_fact_id"] = access_fact
    if resource is not None:
        params["resource_id"] = resource
    if account is not None:
        params["account_id"] = account
    params["limit"] = str(limit)
    url = f"{base_url.rstrip('/')}/api/v0/artifact-bindings"
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
    typer.echo(json.dumps(response.json(), indent=2, default=str))


@artifact_bindings.command("get")
def get_artifact_binding(
    binding_id: str = typer.Argument(..., help="Artifact Binding ID (UUID)"),
    base_url: str = base_url_option(),
) -> None:
    """Get artifact binding by id."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/artifact-bindings/{binding_id}"
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


@access_facts.command("get")
def get_access_fact(
    fact_id: str = typer.Argument(..., help="Access Fact ID (UUID)"),
    base_url: str = base_url_option(),
) -> None:
    """Get access fact by id."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/access-facts/{fact_id}"
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


# ---------------------------------------------------------------------------
# Ownership Assignments sub-commands (added before Initiatives for insert-order clarity)
# ---------------------------------------------------------------------------


@ownership.command("list")
def list_ownership_assignments(
    subject: str | None = typer.Option(None, "--subject", help="Subject ID (UUID)"),
    resource: str | None = typer.Option(None, "--resource", help="Resource ID (UUID)"),
    account: str | None = typer.Option(None, "--account", help="Account ID (UUID)"),
    kind: str | None = typer.Option(
        None, "--kind", help="Filter by kind (primary, secondary, technical)"
    ),
    limit: int = typer.Option(50, "--limit", help="Maximum number of results"),
    base_url: str = base_url_option(),
) -> None:
    """List ownership assignments with optional filters."""
    import httpx

    params: dict[str, str] = {}
    if subject is not None:
        params["subject_id"] = subject
    if resource is not None:
        params["resource_id"] = resource
    if account is not None:
        params["account_id"] = account
    if kind is not None:
        params["kind"] = kind
    params["limit"] = str(limit)
    url = f"{base_url.rstrip('/')}/api/v0/ownership-assignments"
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
    typer.echo(json.dumps(response.json(), indent=2, default=str))


@ownership.command("get")
def get_ownership_assignment(
    assignment_id: str = typer.Argument(..., help="Ownership Assignment ID (UUID)"),
    base_url: str = base_url_option(),
) -> None:
    """Get ownership assignment by id."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/ownership-assignments/{assignment_id}"
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


@ownership.command("create")
def create_ownership_assignment(
    subject: str = typer.Option(..., "--subject", help="Subject ID (UUID)"),
    kind: str = typer.Option(
        ..., "--kind", help="Ownership kind (primary, secondary, technical)"
    ),
    resource: str | None = typer.Option(None, "--resource", help="Resource ID (UUID)"),
    account: str | None = typer.Option(None, "--account", help="Account ID (UUID)"),
    base_url: str = base_url_option(),
) -> None:
    """Create a new ownership assignment (exactly one of --resource or --account required)."""
    import httpx

    if (resource is None) == (account is None):
        typer.echo(
            "Error: exactly one of --resource or --account must be provided.", err=True
        )
        raise typer.Exit(1)

    payload: dict[str, object] = {"subject_id": subject, "kind": kind}
    if resource is not None:
        payload["resource_id"] = resource
    if account is not None:
        payload["account_id"] = account

    url = f"{base_url.rstrip('/')}/api/v0/ownership-assignments"
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
    typer.echo(json.dumps(response.json(), indent=2, default=str))


@ownership.command("delete")
def delete_ownership_assignment(
    assignment_id: str = typer.Argument(..., help="Ownership Assignment ID (UUID)"),
    base_url: str = base_url_option(),
) -> None:
    """Delete an ownership assignment (no output on success)."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/ownership-assignments/{assignment_id}"
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


# ---------------------------------------------------------------------------
# Initiatives sub-commands
# ---------------------------------------------------------------------------


@initiatives.command("list")
def list_initiatives(
    access_fact: str | None = typer.Option(
        None, "--access-fact", help="Access Fact ID (UUID)"
    ),
    type_: str | None = typer.Option(
        None, "--type", help="Filter by initiative type (birthright, requested, ...)"
    ),
    limit: int = typer.Option(50, "--limit", help="Maximum number of results"),
    base_url: str = base_url_option(),
) -> None:
    """List initiatives with optional filters."""
    import httpx

    params: dict[str, str] = {}
    if access_fact is not None:
        params["access_fact_id"] = access_fact
    if type_ is not None:
        params["type"] = type_
    params["limit"] = str(limit)
    url = f"{base_url.rstrip('/')}/api/v0/initiatives"
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
    typer.echo(json.dumps(response.json(), indent=2, default=str))


@initiatives.command("get")
def get_initiative(
    initiative_id: str = typer.Argument(..., help="Initiative ID (UUID)"),
    base_url: str = base_url_option(),
) -> None:
    """Get initiative by id."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/initiatives/{initiative_id}"
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


@initiatives.command("create")
def create_initiative(
    access_fact: str = typer.Option(..., "--access-fact", help="Access Fact ID (UUID)"),
    type_: str = typer.Option(
        ..., "--type", help="Initiative type (birthright, requested, delegated, ...)"
    ),
    origin: str = typer.Option(..., "--origin", help="Free-form origin description"),
    valid_from: str | None = typer.Option(
        None, "--valid-from", help="Validity start (ISO datetime)"
    ),
    valid_until: str | None = typer.Option(
        None, "--valid-until", help="Validity end (ISO datetime)"
    ),
    base_url: str = base_url_option(),
) -> None:
    """Create a new initiative."""
    import httpx

    payload: dict[str, object] = {
        "access_fact_id": access_fact,
        "type": type_,
        "origin": origin,
    }
    if valid_from is not None:
        payload["valid_from"] = valid_from
    if valid_until is not None:
        payload["valid_until"] = valid_until
    url = f"{base_url.rstrip('/')}/api/v0/initiatives"
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
    typer.echo(json.dumps(response.json(), indent=2, default=str))


# ---------------------------------------------------------------------------
# Usage Facts sub-commands
# ---------------------------------------------------------------------------


@usage_facts.command("list")
def list_usage_facts(
    subject: str | None = typer.Option(None, "--subject", help="Subject ID (UUID)"),
    resource: str | None = typer.Option(None, "--resource", help="Resource ID (UUID)"),
    access_fact: str | None = typer.Option(
        None, "--access-fact", help="Access Fact ID (UUID)"
    ),
    since: str | None = typer.Option(
        None, "--since", help="Filter last_seen >= since (ISO datetime)"
    ),
    limit: int = typer.Option(50, "--limit", help="Maximum number of results"),
    base_url: str = base_url_option(),
) -> None:
    """List access usage facts with optional filters."""
    import httpx

    params: dict[str, str] = {}
    if subject is not None:
        params["subject_id"] = subject
    if resource is not None:
        params["resource_id"] = resource
    if access_fact is not None:
        params["access_fact_id"] = access_fact
    if since is not None:
        params["since"] = since
    params["limit"] = str(limit)
    url = f"{base_url.rstrip('/')}/api/v0/access-usage-facts"
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
    typer.echo(json.dumps(response.json(), indent=2, default=str))


@usage_facts.command("get")
def get_usage_fact(
    usage_fact_id: str = typer.Argument(..., help="Access Usage Fact ID (UUID)"),
    base_url: str = base_url_option(),
) -> None:
    """Get access usage fact by id."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/access-usage-facts/{usage_fact_id}"
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


@usage_facts.command("create")
def create_usage_fact(
    access_fact: str = typer.Option(..., "--access-fact", help="Access Fact ID (UUID)"),
    last_seen: str = typer.Option(
        ..., "--last-seen", help="Last seen timestamp (ISO datetime)"
    ),
    usage_count: int = typer.Option(
        ..., "--usage-count", help="Number of usage events in window"
    ),
    window_from: str = typer.Option(
        ..., "--window-from", help="Window start (ISO datetime)"
    ),
    window_to: str | None = typer.Option(
        None,
        "--window-to",
        help="Window end (ISO datetime); omit for open-ended window",
    ),
    base_url: str = base_url_option(),
) -> None:
    """Create a new access usage fact."""
    import httpx

    if usage_count < 0:
        typer.echo("Error: --usage-count must be >= 0.", err=True)
        raise typer.Exit(1)

    payload: dict[str, object] = {
        "access_fact_id": access_fact,
        "last_seen": last_seen,
        "usage_count": usage_count,
        "window_from": window_from,
    }
    if window_to is not None:
        payload["window_to"] = window_to

    url = f"{base_url.rstrip('/')}/api/v0/access-usage-facts"
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
    typer.echo(json.dumps(response.json(), indent=2, default=str))


# ---------------------------------------------------------------------------
# Threat Facts sub-commands
# ---------------------------------------------------------------------------


@threat_facts.command("list")
def list_threat_facts(
    subject: str | None = typer.Option(None, "--subject", help="Subject ID (UUID)"),
    account: str | None = typer.Option(None, "--account", help="Account ID (UUID)"),
    min_risk_score: float | None = typer.Option(
        None, "--min-risk-score", help="Minimum risk score (0.0–1.0)"
    ),
    limit: int = typer.Option(50, "--limit", help="Maximum number of results"),
    base_url: str = base_url_option(),
) -> None:
    """List threat facts with optional filters."""
    import httpx

    if min_risk_score is not None and not (0.0 <= min_risk_score <= 1.0):
        typer.echo("Error: --min-risk-score must be between 0.0 and 1.0.", err=True)
        raise typer.Exit(1)

    params: dict[str, str] = {}
    if subject is not None:
        params["subject_id"] = subject
    if account is not None:
        params["account_id"] = account
    if min_risk_score is not None:
        params["min_risk_score"] = str(min_risk_score)
    params["limit"] = str(limit)
    url = f"{base_url.rstrip('/')}/api/v0/threat-facts"
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
    typer.echo(json.dumps(response.json(), indent=2, default=str))


@threat_facts.command("get")
def get_threat_fact(
    fact_id: str = typer.Argument(..., help="Threat Fact ID (UUID)"),
    base_url: str = base_url_option(),
) -> None:
    """Get threat fact by id."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v0/threat-facts/{fact_id}"
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


@threat_facts.command("upsert")
def upsert_threat_fact(
    subject_id: str = typer.Argument(..., help="Subject ID (UUID)"),
    risk_score: float = typer.Option(..., "--risk-score", help="Risk score (0.0–1.0)"),
    indicator: list[str] = typer.Option(
        default_factory=list,
        help="Active indicator (repeatable: --indicator foo --indicator bar)",
    ),
    account: str | None = typer.Option(
        None, "--account", help="Account ID (UUID) (optional)"
    ),
    last_login_at: str | None = typer.Option(
        None, "--last-login-at", help="Last login timestamp (ISO datetime) (optional)"
    ),
    failed_auth_count: int = typer.Option(
        0, "--failed-auth-count", help="Failed auth count (>= 0)"
    ),
    observed_at: str | None = typer.Option(
        None,
        "--observed-at",
        help="Observed-at timestamp (ISO datetime); server defaults to now",
    ),
    base_url: str = base_url_option(),
) -> None:
    """Upsert a threat fact for a subject (PUT). Returns 201 on first insert, 200 on update."""
    import httpx

    if not (0.0 <= risk_score <= 1.0):
        typer.echo("Error: --risk-score must be between 0.0 and 1.0.", err=True)
        raise typer.Exit(1)
    if failed_auth_count < 0:
        typer.echo("Error: --failed-auth-count must be >= 0.", err=True)
        raise typer.Exit(1)

    payload: dict[str, object] = {
        "risk_score": risk_score,
        "active_indicators": list(indicator),
        "failed_auth_count": failed_auth_count,
    }
    if account is not None:
        payload["account_id"] = account
    if last_login_at is not None:
        payload["last_login_at"] = last_login_at
    if observed_at is not None:
        payload["observed_at"] = observed_at

    url = f"{base_url.rstrip('/')}/api/v0/threat-facts/{subject_id}"
    try:
        with httpx_client() as client:
            response = client.put(url, json=payload)
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


# ---------------------------------------------------------------------------
# Customers sub-commands
# ---------------------------------------------------------------------------


@customers.command("list")
def list_customers(
    plan: str | None = typer.Option(
        None, "--plan", help="Filter by plan tier (free|basic|pro|enterprise)"
    ),
    locked: bool = typer.Option(False, "--locked", help="Show only locked customers"),
    base_url: str = base_url_option(),
) -> None:
    """List customers with optional filters."""
    import httpx

    params: dict[str, str] = {}
    if plan is not None:
        params["plan_tier"] = plan
    if locked:
        params["is_locked"] = "true"
    url = f"{base_url.rstrip('/')}/api/v0/customers"
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
    typer.echo(json.dumps(response.json(), indent=2, default=str))


# ---------------------------------------------------------------------------
# Subjects sub-commands (list) + subject singular get (on parent app)
# ---------------------------------------------------------------------------


@subjects.command("list")
def list_subjects(
    kind: str | None = typer.Option(
        None, "--kind", help="Filter by subject kind (employee|nhi|customer)"
    ),
    status: str | None = typer.Option(
        None, "--status", help="Filter by subject status"
    ),
    base_url: str = base_url_option(),
) -> None:
    """List subjects with optional filters."""
    import httpx

    params: dict[str, str] = {}
    if kind is not None:
        params["kind"] = kind
    if status is not None:
        params["status"] = status
    url = f"{base_url.rstrip('/')}/api/v0/subjects"
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
    typer.echo(json.dumps(response.json(), indent=2, default=str))


@app.command("subject")
def get_subject(
    subject_id: str = typer.Argument(..., help="Subject ID (UUID)"),
    base_url: str = base_url_option(),
) -> None:
    """Show a subject and its attributes."""
    import httpx

    base = base_url.rstrip("/")
    url_subject = f"{base}/api/v0/subjects/{subject_id}"
    url_attrs = f"{base}/api/v0/subjects/{subject_id}/attributes"
    try:
        with httpx_client() as client:
            response_subject = client.get(url_subject)
            try:
                response_subject.raise_for_status()
            except httpx.HTTPStatusError as err:
                typer.echo(f"API error: {err.response.text}", err=True)
                raise typer.Exit(1)
            response_attrs = client.get(url_attrs)
            try:
                response_attrs.raise_for_status()
            except httpx.HTTPStatusError as err:
                typer.echo(f"API error: {err.response.text}", err=True)
                raise typer.Exit(1)
    except httpx.ConnectError:
        handle_connection_error(base_url)
    except httpx.TimeoutException:
        handle_timeout_error(base_url)
    output = {**response_subject.json(), "attributes": response_attrs.json()}
    typer.echo(json.dumps(output, indent=2, default=str))


@initiatives.command("update")
def update_initiative(
    initiative_id: str = typer.Argument(..., help="Initiative ID (UUID)"),
    origin: str | None = typer.Option(None, "--origin", help="New origin description"),
    valid_from: str | None = typer.Option(
        None, "--valid-from", help="New validity start (ISO datetime)"
    ),
    valid_until: str | None = typer.Option(
        None, "--valid-until", help="New validity end (ISO datetime)"
    ),
    base_url: str = base_url_option(),
) -> None:
    """Update an initiative (partial update)."""
    import httpx

    payload: dict[str, object] = {}
    if origin is not None:
        payload["origin"] = origin
    if valid_from is not None:
        payload["valid_from"] = valid_from
    if valid_until is not None:
        payload["valid_until"] = valid_until
    if not payload:
        typer.echo("Nothing to update.", err=True)
        raise typer.Exit(1)
    url = f"{base_url.rstrip('/')}/api/v0/initiatives/{initiative_id}"
    try:
        with httpx_client() as client:
            response = client.patch(url, json=payload)
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
