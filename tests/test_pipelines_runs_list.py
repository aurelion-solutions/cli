"""Tests for al pipelines runs list command."""

import json
from unittest.mock import MagicMock, patch

import httpx
from typer.testing import CliRunner

from conftest import make_mock_http_client
from main import app

runner = CliRunner()

RUNS = [
    {
        "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "pipeline_name": "application_sync",
        "pipeline_version": "1",
        "status": "completed",
        "started_at": "2026-05-11T10:00:00+00:00",
        "finished_at": "2026-05-11T10:00:05+00:00",
    },
]


@patch("al.pipelines.cli.httpx_client")
def test_runs_list_no_filters_text(mock_client_class) -> None:
    """Default invocation sends limit=50 and offset=0 to the API."""
    mock_client_class.return_value = make_mock_http_client("get", return_value=RUNS)

    result = runner.invoke(app, ["pipelines", "runs", "list"])

    assert result.exit_code == 0
    call_url = mock_client_class.return_value.get.call_args[0][0]
    assert "/api/v0/pipeline-runs" in call_url

    call_params = mock_client_class.return_value.get.call_args[1]["params"]
    # params is a list of tuples — normalise to dict for simple assertions
    params_dict = dict(call_params)
    assert params_dict["limit"] == "50"
    assert params_dict["offset"] == "0"
    assert "pipeline_name" not in params_dict


@patch("al.pipelines.cli.httpx_client")
def test_runs_list_all_filters_text(mock_client_class) -> None:
    """All filter flags are forwarded correctly, including repeated --status."""
    mock_client_class.return_value = make_mock_http_client("get", return_value=RUNS)

    result = runner.invoke(
        app,
        [
            "pipelines",
            "runs",
            "list",
            "--pipeline",
            "application_sync",
            "--status",
            "completed",
            "--status",
            "failed",
            "--limit",
            "5",
            "--offset",
            "10",
        ],
    )

    assert result.exit_code == 0
    call_params = mock_client_class.return_value.get.call_args[1]["params"]
    # params is list[tuple[str, str]] — collect values per key
    params_multi: dict[str, list[str]] = {}
    for k, v in call_params:
        params_multi.setdefault(k, []).append(v)

    assert params_multi.get("pipeline_name") == ["application_sync"]
    assert params_multi.get("limit") == ["5"]
    assert params_multi.get("offset") == ["10"]
    assert sorted(params_multi.get("status", [])) == ["completed", "failed"]


@patch("al.pipelines.cli.httpx_client")
def test_runs_list_happy_path_json(mock_client_class) -> None:
    """--format json output round-trips to the mock body."""
    mock_client_class.return_value = make_mock_http_client("get", return_value=RUNS)

    result = runner.invoke(app, ["pipelines", "runs", "list", "--format", "json"])

    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert len(parsed) == 1
    assert parsed[0]["pipeline_name"] == "application_sync"


@patch("al.pipelines.cli.httpx_client")
def test_runs_list_api_500(mock_client_class) -> None:
    """500 from the API → exit 1."""
    error_body = {"detail": "Server Error"}
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

    result = runner.invoke(app, ["pipelines", "runs", "list"])

    assert result.exit_code == 1


@patch("al.pipelines.cli.httpx_client")
def test_runs_list_connection_error(mock_client_class) -> None:
    """Connection refused → exit 1."""
    mock_client_class.side_effect = httpx.ConnectError("Connection refused")

    result = runner.invoke(app, ["pipelines", "runs", "list"])

    assert result.exit_code == 1
    assert "Connection refused" in result.output
