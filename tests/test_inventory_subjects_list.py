"""Tests for al inventory subjects list command."""

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
def test_subjects_list_invokes_get_subjects_endpoint(mock_client_class) -> None:
    """al inventory subjects list calls GET /api/v0/subjects with no params."""
    mock_client = _make_mock_client([])
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["inventory", "subjects", "list"])

    assert result.exit_code == 0
    mock_client.get.assert_called_once()
    call_args = mock_client.get.call_args
    assert "/api/v0/subjects" in str(call_args[0][0])
    assert call_args[1].get("params", {}) == {}


@patch("al.inventory.cli.httpx_client")
def test_subjects_list_with_kind_passes_kind_query(mock_client_class) -> None:
    """--kind employee sends kind=employee in query params."""
    mock_client = _make_mock_client([])
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["inventory", "subjects", "list", "--kind", "employee"])

    assert result.exit_code == 0
    call_kwargs = mock_client.get.call_args[1]
    assert call_kwargs.get("params", {}).get("kind") == "employee"


@patch("al.inventory.cli.httpx_client")
def test_subjects_list_with_status_passes_status_query(mock_client_class) -> None:
    """--status active sends status=active in query params."""
    mock_client = _make_mock_client([])
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["inventory", "subjects", "list", "--status", "active"])

    assert result.exit_code == 0
    call_kwargs = mock_client.get.call_args[1]
    assert call_kwargs.get("params", {}).get("status") == "active"


@patch("al.inventory.cli.httpx_client")
def test_subjects_list_with_both_filters_passes_both_params(mock_client_class) -> None:
    """--kind customer --status verified sends both params."""
    mock_client = _make_mock_client([])
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app,
        ["inventory", "subjects", "list", "--kind", "customer", "--status", "verified"],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.get.call_args[1]
    params = call_kwargs.get("params", {})
    assert params.get("kind") == "customer"
    assert params.get("status") == "verified"


@patch("al.inventory.cli.httpx_client")
def test_subjects_list_prints_response_as_indented_json(mock_client_class) -> None:
    """Output is the mocked response body as indented JSON."""
    body = [{"id": "xyz", "kind": "employee"}]
    mock_client = _make_mock_client(body)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["inventory", "subjects", "list"])

    assert result.exit_code == 0
    assert json.loads(result.output) == body


@patch("al.inventory.cli.httpx_client")
def test_subjects_list_connection_refused_exits_1(mock_client_class) -> None:
    """ConnectError causes exit 1 and mentions Connection refused."""
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.ConnectError("refused")
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["inventory", "subjects", "list"])

    assert result.exit_code == 1
    assert "Connection refused" in result.output


@patch("al.inventory.cli.httpx_client")
def test_subjects_list_timeout_exits_1(mock_client_class) -> None:
    """TimeoutException causes exit 1 and mentions timed out."""
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.TimeoutException("timeout")
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["inventory", "subjects", "list"])

    assert result.exit_code == 1
    assert "timed out" in result.output.lower()
