"""Tests for al findings list command."""

import json
from unittest.mock import MagicMock, patch

import httpx
from typer.testing import CliRunner

from main import app

runner = CliRunner()

FINDINGS = [
    {
        "id": 1,
        "kind": "sod",
        "severity": "high",
        "status": "open",
        "rule_id": 10,
    }
]
SUBJECT_UUID = "11111111-1111-1111-1111-111111111111"


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


@patch("al.findings.cli.httpx_client")
def test_findings_list_no_filters(mock_client_class) -> None:
    mock_client = _make_mock_client(200, FINDINGS)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["findings", "list"])

    assert result.exit_code == 0
    call_url = mock_client.get.call_args[0][0]
    assert "/api/v0/findings" in call_url
    call_params = mock_client.get.call_args[1]["params"]
    assert call_params["limit"] == "50"


@patch("al.findings.cli.httpx_client")
def test_findings_list_all_filters(mock_client_class) -> None:
    mock_client = _make_mock_client(200, FINDINGS)
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app,
        [
            "findings",
            "list",
            "--scan-run",
            "5",
            "--rule",
            "10",
            "--severity",
            "high",
            "--status",
            "open",
            "--kind",
            "sod",
            "--subject",
            SUBJECT_UUID,
            "--limit",
            "25",
            "--offset",
            "10",
        ],
    )

    assert result.exit_code == 0
    call_params = mock_client.get.call_args[1]["params"]
    assert call_params["scan_run_id"] == "5"
    assert call_params["rule_id"] == "10"
    assert call_params["severity"] == "high"
    assert call_params["status"] == "open"
    assert call_params["kind"] == "sod"
    assert call_params["subject_id"] == SUBJECT_UUID
    assert call_params["limit"] == "25"
    assert call_params["offset"] == "10"


@patch("al.findings.cli.httpx_client")
def test_findings_list_api_error(mock_client_class) -> None:
    mock_client = _make_mock_client(500, {"detail": "Internal Server Error"})
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["findings", "list"])

    assert result.exit_code == 1
    assert "API error:" in result.output


@patch("al.findings.cli.httpx_client")
def test_findings_list_connection_error(mock_client_class) -> None:
    mock_client_class.side_effect = httpx.ConnectError("Connection refused")

    result = runner.invoke(app, ["findings", "list"])

    assert result.exit_code == 1
    assert "Connection refused" in result.output
