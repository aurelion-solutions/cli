"""Tests for al llm profile * commands."""

import json
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from main import app

runner = CliRunner()

PROFILE_ID = "aaaaaaaa-0000-0000-0000-000000000001"
MODEL_ID = "bbbbbbbb-0000-0000-0000-000000000002"


def _mock_client(method: str, return_value=None, status_code: int = 200):
    """Return a mock httpx_client context manager for the given HTTP method."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = return_value or {}
    mock_response.status_code = status_code

    mock_client = MagicMock()
    getattr(mock_client, method).return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    return mock_client


@patch("al.llm.cli.httpx_client")
def test_list_calls_correct_endpoint(mock_client_class):
    """al llm profile list issues GET /api/v0/llm/execution-profiles."""
    profiles = [{"id": PROFILE_ID, "name": "deterministic", "model_id": MODEL_ID}]
    mock_client_class.return_value = _mock_client("get", return_value=profiles)

    result = runner.invoke(app, ["llm", "profile", "list"])

    assert result.exit_code == 0
    call_args = mock_client_class.return_value.get.call_args
    assert "/api/v0/llm/execution-profiles" in str(call_args[0][0])
    assert PROFILE_ID in result.output


@patch("al.llm.cli.httpx_client")
def test_show_renders_json(mock_client_class):
    """al llm profile show <id> prints the profile as JSON."""
    profile = {
        "id": PROFILE_ID,
        "name": "deterministic",
        "model_id": MODEL_ID,
        "param_overrides": {"temperature": 0.0},
        "created_at": "2026-04-25T00:00:00Z",
        "updated_at": "2026-04-25T00:00:00Z",
    }
    mock_client_class.return_value = _mock_client("get", return_value=profile)

    result = runner.invoke(app, ["llm", "profile", "show", PROFILE_ID])

    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["id"] == PROFILE_ID
    assert parsed["param_overrides"] == {"temperature": 0.0}


@patch("al.llm.cli.httpx_client")
def test_create_sends_payload(mock_client_class):
    """al llm profile create sends POST with all three fields."""
    created = {
        "id": PROFILE_ID,
        "name": "creative",
        "model_id": MODEL_ID,
        "param_overrides": {},
    }
    mock_client_class.return_value = _mock_client(
        "post", return_value=created, status_code=201
    )

    result = runner.invoke(
        app,
        [
            "llm",
            "profile",
            "create",
            "--name",
            "creative",
            "--model-id",
            MODEL_ID,
            "--param-overrides",
            '{"temperature": 1.0}',
        ],
    )

    assert result.exit_code == 0
    call_args = mock_client_class.return_value.post.call_args
    assert "/api/v0/llm/execution-profiles" in str(call_args[0][0])
    payload = call_args[1]["json"]
    assert payload["name"] == "creative"
    assert payload["model_id"] == MODEL_ID
    assert payload["param_overrides"] == {"temperature": 1.0}


@patch("al.llm.cli.httpx_client")
def test_update_sends_only_set_fields(mock_client_class):
    """al llm profile update <id> --name X sends PATCH body with only name (no param_overrides)."""
    updated = {
        "id": PROFILE_ID,
        "name": "renamed",
        "model_id": MODEL_ID,
        "param_overrides": {},
        "created_at": "2026-04-25T00:00:00Z",
        "updated_at": "2026-04-25T00:00:00Z",
    }
    mock_client_class.return_value = _mock_client("patch", return_value=updated)

    result = runner.invoke(
        app,
        ["llm", "profile", "update", PROFILE_ID, "--name", "renamed"],
    )

    assert result.exit_code == 0
    call_args = mock_client_class.return_value.patch.call_args
    payload = call_args[1]["json"]
    assert payload == {"name": "renamed"}
    assert "param_overrides" not in payload


@patch("al.llm.cli.httpx_client")
def test_delete_requires_yes_flag(mock_client_class):
    """Without --yes exit code != 0 and DELETE is not called; with --yes DELETE is called."""
    mock_client_class.return_value = _mock_client("delete", status_code=204)
    mock_client_class.return_value.delete.return_value.status_code = 204

    # Without --yes
    result_no = runner.invoke(app, ["llm", "profile", "delete", PROFILE_ID])
    assert result_no.exit_code != 0
    mock_client_class.return_value.delete.assert_not_called()

    # With --yes
    result_yes = runner.invoke(app, ["llm", "profile", "delete", PROFILE_ID, "--yes"])
    assert result_yes.exit_code == 0
    mock_client_class.return_value.delete.assert_called_once()
    call_url = mock_client_class.return_value.delete.call_args[0][0]
    assert f"/api/v0/llm/execution-profiles/{PROFILE_ID}" in call_url
