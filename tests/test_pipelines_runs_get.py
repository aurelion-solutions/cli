"""Tests for al pipelines runs get command."""

import json
from unittest.mock import MagicMock, patch

import httpx
from typer.testing import CliRunner

from conftest import make_mock_http_client
from main import app

runner = CliRunner()

RUN_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"

RUN_DETAIL = {
    "id": RUN_ID,
    "pipeline_name": "application_sync",
    "pipeline_version": "1",
    "status": "completed",
    "trigger_source": "mq",
    "current_step": None,
    "started_at": "2026-05-11T10:00:00+00:00",
    "finished_at": "2026-05-11T10:00:05+00:00",
    "error": None,
    "args": {"application_id": "11111111-1111-1111-1111-111111111111"},
    "steps": [
        {
            "step_name": "reconcile",
            "attempt": 1,
            "status": "completed",
            "started_at": "2026-05-11T10:00:01+00:00",
            "finished_at": "2026-05-11T10:00:03+00:00",
        }
    ],
}


@patch("al.pipelines.cli.httpx_client")
def test_runs_get_happy_path_text(mock_client_class) -> None:
    """Get run as text — run id, pipeline_name, status, and step line are present."""
    mock_client_class.return_value = make_mock_http_client(
        "get", return_value=RUN_DETAIL
    )

    result = runner.invoke(app, ["pipelines", "runs", "get", RUN_ID])

    assert result.exit_code == 0
    assert RUN_ID in result.output
    assert "application_sync" in result.output
    assert "completed" in result.output
    assert "reconcile" in result.output


@patch("al.pipelines.cli.httpx_client")
def test_runs_get_happy_path_json(mock_client_class) -> None:
    """Get run as JSON — output round-trips to the mock body."""
    mock_client_class.return_value = make_mock_http_client(
        "get", return_value=RUN_DETAIL
    )

    result = runner.invoke(
        app, ["pipelines", "runs", "get", RUN_ID, "--format", "json"]
    )

    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["id"] == RUN_ID
    assert parsed["pipeline_name"] == "application_sync"


@patch("al.pipelines.cli.httpx_client")
def test_runs_get_404(mock_client_class) -> None:
    """404 from the API → exit 1 with 'not found' in output."""
    error_body = {"detail": "Pipeline run not found"}
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

    result = runner.invoke(app, ["pipelines", "runs", "get", RUN_ID])

    assert result.exit_code == 1
    combined = result.output + (result.stderr or "")
    assert "not found" in combined.lower()


def test_runs_get_invalid_uuid() -> None:
    """Invalid UUID positional arg → Typer exits 2 (argument parsing failure)."""
    result = runner.invoke(app, ["pipelines", "runs", "get", "not-a-uuid"])

    assert result.exit_code == 2
