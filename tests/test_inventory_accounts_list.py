"""Tests for al inventory accounts list command."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from main import app

runner = CliRunner()


@patch("al.inventory.cli.httpx_client")
def test_accounts_list_invokes_get_endpoint(mock_client_class) -> None:
    """al inventory accounts list invokes GET /api/v0/accounts."""
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["inventory", "accounts", "list"])

    assert result.exit_code == 0
    mock_client.get.assert_called_once()
    call_args = mock_client.get.call_args
    assert "/api/v0/accounts" in str(call_args[0][0])


@patch("al.inventory.cli.httpx_client")
def test_accounts_list_with_status_filter_passes_params(mock_client_class) -> None:
    """al inventory accounts list --status active passes status param."""
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["inventory", "accounts", "list", "--status", "active"])

    assert result.exit_code == 0
    mock_client.get.assert_called_once()
    call_kwargs = mock_client.get.call_args[1]
    assert call_kwargs.get("params", {}).get("status") == "active"
