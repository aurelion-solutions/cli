"""Tests for al inventory customers list command."""

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
def test_customers_list_invokes_get_customers_endpoint(mock_client_class) -> None:
    """al inventory customers list calls GET /api/v0/customers with no params."""
    mock_client = _make_mock_client([])
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["inventory", "customers", "list"])

    assert result.exit_code == 0
    mock_client.get.assert_called_once()
    call_args = mock_client.get.call_args
    assert "/api/v0/customers" in str(call_args[0][0])
    assert call_args[1].get("params", {}) == {}


@patch("al.inventory.cli.httpx_client")
def test_customers_list_with_plan_passes_plan_tier_query(mock_client_class) -> None:
    """--plan pro sends plan_tier=pro in query params."""
    mock_client = _make_mock_client([])
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["inventory", "customers", "list", "--plan", "pro"])

    assert result.exit_code == 0
    call_kwargs = mock_client.get.call_args[1]
    assert call_kwargs.get("params", {}).get("plan_tier") == "pro"


@patch("al.inventory.cli.httpx_client")
def test_customers_list_with_locked_passes_is_locked_true(mock_client_class) -> None:
    """--locked sends is_locked=true in query params."""
    mock_client = _make_mock_client([])
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["inventory", "customers", "list", "--locked"])

    assert result.exit_code == 0
    call_kwargs = mock_client.get.call_args[1]
    assert call_kwargs.get("params", {}).get("is_locked") == "true"


@patch("al.inventory.cli.httpx_client")
def test_customers_list_without_locked_flag_does_not_send_is_locked(
    mock_client_class,
) -> None:
    """Absence of --locked means is_locked is NOT sent."""
    mock_client = _make_mock_client([])
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["inventory", "customers", "list"])

    assert result.exit_code == 0
    call_kwargs = mock_client.get.call_args[1]
    assert "is_locked" not in call_kwargs.get("params", {})


@patch("al.inventory.cli.httpx_client")
def test_customers_list_with_both_filters_passes_both_params(mock_client_class) -> None:
    """--plan enterprise --locked sends both plan_tier and is_locked."""
    mock_client = _make_mock_client([])
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app, ["inventory", "customers", "list", "--plan", "enterprise", "--locked"]
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.get.call_args[1]
    params = call_kwargs.get("params", {})
    assert params.get("plan_tier") == "enterprise"
    assert params.get("is_locked") == "true"


@patch("al.inventory.cli.httpx_client")
def test_customers_list_prints_response_as_indented_json(mock_client_class) -> None:
    """Output is the mocked response body as indented JSON."""
    body = [{"id": "abc", "name": "Acme Corp"}]
    mock_client = _make_mock_client(body)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["inventory", "customers", "list"])

    assert result.exit_code == 0
    assert json.loads(result.output) == body


@patch("al.inventory.cli.httpx_client")
def test_customers_list_connection_refused_exits_1(mock_client_class) -> None:
    """ConnectError causes exit 1 and mentions Connection refused."""
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.ConnectError("refused")
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["inventory", "customers", "list"])

    assert result.exit_code == 1
    assert "Connection refused" in result.output


@patch("al.inventory.cli.httpx_client")
def test_customers_list_timeout_exits_1(mock_client_class) -> None:
    """TimeoutException causes exit 1 and mentions timed out."""
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.TimeoutException("timeout")
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["inventory", "customers", "list"])

    assert result.exit_code == 1
    assert "timed out" in result.output.lower()
