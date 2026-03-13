"""Tests for al secrets list command."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from main import app

runner = CliRunner()


@patch("al.secrets.cli.httpx_client")
def test_secrets_list_invokes_get_endpoint(mock_client_class):
    """al secrets list invokes GET /secrets."""
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {"key": "github/token", "provider": "file", "namespace": "default"},
        {"key": "db/password", "provider": "file", "namespace": "prod"},
    ]
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["secrets", "list"])

    assert result.exit_code == 0
    mock_client.get.assert_called_once()
    call_args = mock_client.get.call_args
    assert "/api/v0/secrets" in str(call_args[0][0])
    assert "github/token" in result.output
    assert "db/password" in result.output


@patch("al.secrets.cli.httpx_client")
def test_secrets_list_shows_no_secrets_when_empty(mock_client_class):
    """al secrets list shows 'No secrets' when list is empty."""
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["secrets", "list"])

    assert result.exit_code == 0
    assert "No secrets" in result.output
