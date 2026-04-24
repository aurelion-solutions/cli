"""Tests for al scan run command."""

import json
from unittest.mock import MagicMock, patch

import httpx
from typer.testing import CliRunner

from main import app

runner = CliRunner()

CREATE_RESPONSE = {
    "id": 42,
    "status": "pending",
    "triggered_by": "manual",
}
RUN_RESPONSE = {
    "id": 42,
    "status": "completed",
    "triggered_by": "manual",
    "findings_created_count": 3,
    "findings_reused_count": 1,
}


def _make_two_call_client(
    create_status: int,
    create_body: object,
    run_status: int,
    run_body: object,
) -> MagicMock:
    """Build a mock client where the first POST returns create_* and the second POST returns run_*."""

    def make_response(status_code: int, json_body: object) -> MagicMock:
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = json_body
        resp.text = json.dumps(json_body)
        if status_code >= 400:
            resp.raise_for_status.side_effect = httpx.HTTPStatusError(
                message=f"HTTP {status_code}",
                request=MagicMock(),
                response=resp,
            )
        else:
            resp.raise_for_status = MagicMock()
        return resp

    resp_create = make_response(create_status, create_body)
    resp_run = make_response(run_status, run_body)

    mock_client = MagicMock()
    mock_client.post.side_effect = [resp_create, resp_run]
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    return mock_client


@patch("al.scan.cli.httpx_client")
def test_scan_run_happy_path(mock_client_class) -> None:
    mock_client = _make_two_call_client(201, CREATE_RESPONSE, 200, RUN_RESPONSE)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["scan", "run"])

    assert result.exit_code == 0
    assert mock_client.post.call_count == 2
    # First call creates the run
    first_call_url = mock_client.post.call_args_list[0][0][0]
    assert "/api/v0/scan-runs" in first_call_url
    assert "/run" not in first_call_url
    # Second call executes it
    second_call_url = mock_client.post.call_args_list[1][0][0]
    assert "/api/v0/scan-runs/42/run" in second_call_url
    # Output is the run response
    assert "completed" in result.output


@patch("al.scan.cli.httpx_client")
def test_scan_run_default_triggered_by_manual(mock_client_class) -> None:
    mock_client = _make_two_call_client(201, CREATE_RESPONSE, 200, RUN_RESPONSE)
    mock_client_class.return_value = mock_client

    runner.invoke(app, ["scan", "run"])

    create_body = mock_client.post.call_args_list[0][1]["json"]
    assert create_body["triggered_by"] == "manual"


@patch("al.scan.cli.httpx_client")
def test_scan_run_create_fails_422(mock_client_class) -> None:
    """If step 1 (create) fails, step 2 must NOT be called."""

    def make_response(status_code: int, json_body: object) -> MagicMock:
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = json_body
        resp.text = json.dumps(json_body)
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            message=f"HTTP {status_code}",
            request=MagicMock(),
            response=resp,
        )
        return resp

    mock_client = MagicMock()
    mock_client.post.return_value = make_response(422, {"detail": "bad subject"})
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["scan", "run"])

    assert result.exit_code == 1
    assert mock_client.post.call_count == 1


@patch("al.scan.cli.httpx_client")
def test_scan_run_execute_fails_409(mock_client_class) -> None:
    """If step 2 (run) fails, surface the scan run id in stderr."""
    mock_client = _make_two_call_client(
        201, CREATE_RESPONSE, 409, {"detail": "already running"}
    )
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["scan", "run"])

    assert result.exit_code == 1
    # Orphan run id must appear in the output for operator visibility
    assert "42" in result.output


@patch("al.scan.cli.httpx_client")
def test_scan_run_connection_error(mock_client_class) -> None:
    mock_client_class.side_effect = httpx.ConnectError("Connection refused")

    result = runner.invoke(app, ["scan", "run"])

    assert result.exit_code == 1
    assert "Connection refused" in result.output
