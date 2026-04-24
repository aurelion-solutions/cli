"""Tests for al scan list command."""

import json
from unittest.mock import MagicMock, patch

import httpx
from typer.testing import CliRunner

from main import app

runner = CliRunner()

SCAN_RUNS = [
    {"id": 1, "status": "completed", "triggered_by": "manual"},
    {"id": 2, "status": "failed", "triggered_by": "schedule"},
]


def _make_mock_client(status_code: int, json_body: object) -> MagicMock:
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_body
    mock_response.text = json.dumps(json_body)

    if status_code >= 400:
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message=f"HTTP {status_code}",
            request=MagicMock(),
            response=mock_response,
        )
    else:
        mock_response.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    return mock_client


@patch("al.scan.cli.httpx_client")
def test_scan_list_no_filters(mock_client_class) -> None:
    mock_client = _make_mock_client(200, SCAN_RUNS)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["scan", "list"])

    assert result.exit_code == 0
    call_url = mock_client.get.call_args[0][0]
    assert "/api/v0/scan-runs" in call_url
    call_params = mock_client.get.call_args[1]["params"]
    assert call_params["limit"] == "50"


@patch("al.scan.cli.httpx_client")
def test_scan_list_with_status_and_triggered_by(mock_client_class) -> None:
    mock_client = _make_mock_client(200, SCAN_RUNS)
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app, ["scan", "list", "--status", "completed", "--triggered-by", "manual"]
    )

    assert result.exit_code == 0
    call_params = mock_client.get.call_args[1]["params"]
    assert call_params["status"] == "completed"
    assert call_params["triggered_by"] == "manual"


@patch("al.scan.cli.httpx_client")
def test_scan_list_custom_limit(mock_client_class) -> None:
    mock_client = _make_mock_client(200, SCAN_RUNS)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["scan", "list", "--limit", "9999"])

    assert result.exit_code == 0
    call_params = mock_client.get.call_args[1]["params"]
    # No client-side cap — pass through verbatim
    assert call_params["limit"] == "9999"


@patch("al.scan.cli.httpx_client")
def test_scan_list_api_error(mock_client_class) -> None:
    mock_client = _make_mock_client(500, {"detail": "Internal Server Error"})
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["scan", "list"])

    assert result.exit_code == 1
    assert "API error:" in result.output
