"""Tests for al inventory action <slug> command."""

import json
from unittest.mock import MagicMock, patch

import httpx
from typer.testing import CliRunner

from main import app

runner = CliRunner()

ACTION_BODY = {
    "id": 1,
    "slug": "read",
    "description": "Observe a resource without modifying it.",
    "created_at": "2026-04-24T00:00:00+00:00",
}


def _make_ok_response(body):
    resp = MagicMock()
    resp.json.return_value = body
    resp.raise_for_status = MagicMock()
    return resp


def _make_error_response(status_code: int, text: str):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    error = httpx.HTTPStatusError(
        message=f"{status_code}",
        request=MagicMock(),
        response=MagicMock(text=text, status_code=status_code),
    )
    resp.raise_for_status = MagicMock(side_effect=error)
    return resp


@patch("al.inventory.cli.httpx_client")
def test_action_get_calls_action_by_slug_endpoint(mock_client_class) -> None:
    """al inventory action read calls GET /api/v0/actions/read."""
    mock_client = MagicMock()
    mock_client.get.return_value = _make_ok_response(ACTION_BODY)
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["inventory", "action", "read"])

    assert result.exit_code == 0
    assert mock_client.get.call_count == 1
    url_called = mock_client.get.call_args[0][0]
    assert "/api/v0/actions/read" in url_called


@patch("al.inventory.cli.httpx_client")
def test_action_get_prints_response_as_indented_json(mock_client_class) -> None:
    """Output is the mocked response body as indented JSON."""
    mock_client = MagicMock()
    mock_client.get.return_value = _make_ok_response(ACTION_BODY)
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["inventory", "action", "read"])

    assert result.exit_code == 0
    assert json.loads(result.output) == ACTION_BODY


@patch("al.inventory.cli.httpx_client")
def test_action_get_404_exits_1(mock_client_class) -> None:
    """404 response causes exit 1 and prints API error."""
    mock_client = MagicMock()
    mock_client.get.return_value = _make_error_response(
        404, '{"detail": "Action not found"}'
    )
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["inventory", "action", "nonexistent"])

    assert result.exit_code == 1
    assert "API error" in result.output


@patch("al.inventory.cli.httpx_client")
def test_action_get_connection_refused_exits_1(mock_client_class) -> None:
    """ConnectError causes exit 1 and mentions Connection refused."""
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.ConnectError("refused")
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["inventory", "action", "read"])

    assert result.exit_code == 1
    assert "Connection refused" in result.output
