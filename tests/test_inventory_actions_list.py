"""Tests for al inventory actions list command."""

import json
from unittest.mock import MagicMock, patch

import httpx
from typer.testing import CliRunner

from main import app

runner = CliRunner()


def _make_mock_client(return_value):
    mock_response = MagicMock()
    mock_response.json.return_value = return_value
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    return mock_client


@patch("al.inventory.cli.httpx_client")
def test_actions_list_invokes_get_actions_endpoint(mock_client_class) -> None:
    """al inventory actions list calls GET /api/v0/actions."""
    mock_client = _make_mock_client([])
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["inventory", "actions", "list"])

    assert result.exit_code == 0
    mock_client.get.assert_called_once()
    call_args = mock_client.get.call_args
    assert "/api/v0/actions" in str(call_args[0][0])


@patch("al.inventory.cli.httpx_client")
def test_actions_list_passes_no_query_params(mock_client_class) -> None:
    """al inventory actions list sends no query parameters."""
    mock_client = _make_mock_client([])
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["inventory", "actions", "list"])

    assert result.exit_code == 0
    call_kwargs = mock_client.get.call_args[1]
    assert "params" not in call_kwargs


@patch("al.inventory.cli.httpx_client")
def test_actions_list_prints_response_as_indented_json(mock_client_class) -> None:
    """Output is the mocked response body as indented JSON."""
    body = [
        {
            "id": 1,
            "slug": "read",
            "description": "Observe a resource without modifying it.",
            "created_at": "2026-04-24T00:00:00+00:00",
        },
        {
            "id": 2,
            "slug": "write",
            "description": "Modify a resource.",
            "created_at": "2026-04-24T00:00:00+00:00",
        },
    ]
    mock_client = _make_mock_client(body)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["inventory", "actions", "list"])

    assert result.exit_code == 0
    assert json.loads(result.output) == body


@patch("al.inventory.cli.httpx_client")
def test_actions_list_connection_refused_exits_1(mock_client_class) -> None:
    """ConnectError causes exit 1 and mentions Connection refused."""
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.ConnectError("refused")
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["inventory", "actions", "list"])

    assert result.exit_code == 1
    assert "Connection refused" in result.output


@patch("al.inventory.cli.httpx_client")
def test_actions_list_timeout_exits_1(mock_client_class) -> None:
    """TimeoutException causes exit 1 and mentions timed out."""
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.TimeoutException("timeout")
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["inventory", "actions", "list"])

    assert result.exit_code == 1
    assert "timed out" in result.output.lower()
