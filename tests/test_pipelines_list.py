"""Tests for al pipelines list command."""

import json
from unittest.mock import MagicMock, patch

import httpx
from typer.testing import CliRunner

from conftest import make_mock_http_client
from main import app

runner = CliRunner()

PIPELINES = [
    {
        "name": "application_sync",
        "version": "1",
        "schema_version": 1,
        "description": "Sync application",
        "step_count": 3,
        "triggers": [{"type": "mq"}],
    },
    {
        "name": "access_review",
        "version": "2",
        "schema_version": 1,
        "description": "Review access",
        "step_count": 5,
        "triggers": [],
    },
]


@patch("al.pipelines.cli.httpx_client")
def test_list_happy_path_text(mock_client_class) -> None:
    """List pipelines as text — both names and steps= token are present."""
    mock_client_class.return_value = make_mock_http_client(
        "get", return_value=PIPELINES
    )

    result = runner.invoke(app, ["pipelines", "list"])

    assert result.exit_code == 0
    assert "application_sync" in result.output
    assert "access_review" in result.output
    assert "steps=" in result.output


@patch("al.pipelines.cli.httpx_client")
def test_list_happy_path_json(mock_client_class) -> None:
    """List pipelines as JSON — output round-trips to the mock body."""
    mock_client_class.return_value = make_mock_http_client(
        "get", return_value=PIPELINES
    )

    result = runner.invoke(app, ["pipelines", "list", "--format", "json"])

    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert len(parsed) == 2
    assert parsed[0]["name"] == "application_sync"


@patch("al.pipelines.cli.httpx_client")
def test_list_api_500(mock_client_class) -> None:
    """500 from the API → exit 1 with API error in stderr."""
    error_body = {"detail": "Internal Server Error"}
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = json.dumps(error_body)
    exc = httpx.HTTPStatusError(
        message="HTTP 500",
        request=MagicMock(),
        response=mock_response,
    )
    mock_client_class.return_value = make_mock_http_client(
        "get", return_value=error_body, status_code=500, raise_for_status_exc=exc
    )

    result = runner.invoke(app, ["pipelines", "list"])

    assert result.exit_code == 1
    combined = result.output + (result.stderr or "")
    assert "API error" in combined


@patch("al.pipelines.cli.httpx_client")
def test_list_connection_error(mock_client_class) -> None:
    """Connection refused → exit 1 with Connection refused in output."""
    mock_client_class.side_effect = httpx.ConnectError("Connection refused")

    result = runner.invoke(app, ["pipelines", "list"])

    assert result.exit_code == 1
    assert "Connection refused" in result.output
