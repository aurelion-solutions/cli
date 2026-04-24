"""Tests for al sod evaluate command."""

import json
from unittest.mock import MagicMock, patch

import httpx
from typer.testing import CliRunner

from main import app

runner = CliRunner()

SUBJECT_UUID = "11111111-1111-1111-1111-111111111111"
VIOLATIONS_RESPONSE = [
    {
        "rule_id": 1,
        "rule_code": "FIN-001",
        "severity": "high",
        "is_mitigated": False,
    }
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
    mock_client.post.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    return mock_client


@patch("al.sod.cli.httpx_client")
def test_evaluate_with_at(mock_client_class) -> None:
    mock_client = _make_mock_client(200, VIOLATIONS_RESPONSE)
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app,
        ["sod", "evaluate", SUBJECT_UUID, "--at", "2026-04-24T12:00:00+00:00"],
    )

    assert result.exit_code == 0
    mock_client.post.assert_called_once()
    call_url = mock_client.post.call_args[0][0]
    assert "/api/v0/sod/evaluate" in call_url
    call_body = mock_client.post.call_args[1]["json"]
    assert call_body["subject_id"] == SUBJECT_UUID
    assert call_body["at"] == "2026-04-24T12:00:00+00:00"
    assert "FIN-001" in result.output


@patch("al.sod.cli.httpx_client")
def test_evaluate_without_at_omits_key(mock_client_class) -> None:
    mock_client = _make_mock_client(200, VIOLATIONS_RESPONSE)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["sod", "evaluate", SUBJECT_UUID])

    assert result.exit_code == 0
    call_body = mock_client.post.call_args[1]["json"]
    assert "at" not in call_body


@patch("al.sod.cli.httpx_client")
def test_evaluate_api_error_500(mock_client_class) -> None:
    mock_client = _make_mock_client(500, {"detail": "Internal Server Error"})
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["sod", "evaluate", SUBJECT_UUID])

    assert result.exit_code == 1
    assert "API error:" in result.output


@patch("al.sod.cli.httpx_client")
def test_evaluate_connection_refused(mock_client_class) -> None:
    mock_client_class.side_effect = httpx.ConnectError("Connection refused")

    result = runner.invoke(app, ["sod", "evaluate", SUBJECT_UUID])

    assert result.exit_code == 1
    assert "Connection refused" in result.output


@patch("al.sod.cli.httpx_client")
def test_evaluate_timeout(mock_client_class) -> None:
    mock_client_class.side_effect = httpx.TimeoutException("Timeout")

    result = runner.invoke(app, ["sod", "evaluate", SUBJECT_UUID])

    assert result.exit_code == 1
    assert "timed out" in result.output


@patch("al.sod.cli.httpx_client")
def test_evaluate_empty_response(mock_client_class) -> None:
    mock_client = _make_mock_client(200, [])
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["sod", "evaluate", SUBJECT_UUID])

    assert result.exit_code == 0
    assert "[]" in result.output
