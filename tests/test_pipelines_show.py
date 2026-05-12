"""Tests for al pipelines show command."""

import json
from unittest.mock import MagicMock, patch

import httpx
from typer.testing import CliRunner

from conftest import make_mock_http_client
from main import app

runner = CliRunner()

PIPELINE_DETAIL = {
    "name": "application_sync",
    "version": "1",
    "schema_version": 1,
    "description": "Sync application",
    "step_count": 2,
    "triggers": [{"type": "mq", "exchange": "aurelion.events"}],
    "args_schema": {},
    "content_hash": "abc123def456",
    "source_path": "pipelines/application_sync.yaml",
    "steps": [
        {"id": "reconcile", "engine": "reconciliation", "action": "run"},
        {"id": "sync", "engine": "sync_apply", "action": "apply"},
    ],
}


@patch("al.pipelines.cli.httpx_client")
def test_show_happy_path_text(mock_client_class) -> None:
    """Show pipeline as text — name, version, content_hash and step line are present."""
    mock_client_class.return_value = make_mock_http_client(
        "get", return_value=PIPELINE_DETAIL
    )

    result = runner.invoke(app, ["pipelines", "show", "application_sync"])

    assert result.exit_code == 0
    assert "application_sync" in result.output
    assert "abc123def456" in result.output
    assert "reconcile" in result.output


@patch("al.pipelines.cli.httpx_client")
def test_show_happy_path_json(mock_client_class) -> None:
    """Show pipeline as JSON — output round-trips to the mock body."""
    mock_client_class.return_value = make_mock_http_client(
        "get", return_value=PIPELINE_DETAIL
    )

    result = runner.invoke(
        app, ["pipelines", "show", "application_sync", "--format", "json"]
    )

    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["name"] == "application_sync"
    assert parsed["content_hash"] == "abc123def456"


@patch("al.pipelines.cli.httpx_client")
def test_show_404(mock_client_class) -> None:
    """404 from the API → exit 1 with 'not loaded' in output."""
    error_body = {"detail": "Pipeline 'foo' not loaded"}
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = json.dumps(error_body)
    exc = httpx.HTTPStatusError(
        message="HTTP 404",
        request=MagicMock(),
        response=mock_response,
    )
    mock_client_class.return_value = make_mock_http_client(
        "get", return_value=error_body, status_code=404, raise_for_status_exc=exc
    )

    result = runner.invoke(app, ["pipelines", "show", "foo"])

    assert result.exit_code == 1
    combined = result.output + (result.stderr or "")
    assert "not loaded" in combined


@patch("al.pipelines.cli.httpx_client")
def test_show_connection_error(mock_client_class) -> None:
    """Connection refused → exit 1."""
    mock_client_class.side_effect = httpx.ConnectError("Connection refused")

    result = runner.invoke(app, ["pipelines", "show", "application_sync"])

    assert result.exit_code == 1
    assert "Connection refused" in result.output
