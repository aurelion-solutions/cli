"""Tests for al secrets delete command."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from main import app

runner = CliRunner()


@patch("al.secrets.cli.httpx_client")
def test_secrets_delete_invokes_delete_endpoint(mock_client_class):
    """al secrets delete invokes DELETE /secrets/{provider}/{key}."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.delete.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app,
        [
            "secrets",
            "delete",
            "--key",
            "github/token",
            "--provider",
            "file",
            "--namespace",
            "default",
        ],
    )

    assert result.exit_code == 0
    mock_client.delete.assert_called_once()
    call_args = mock_client.delete.call_args
    assert "/api/v0/secrets/file/" in str(call_args[0][0])
    assert "github" in str(call_args[0][0])
    assert call_args[1]["params"] == {"namespace": "default"}
    assert "Secret deleted" in result.output
