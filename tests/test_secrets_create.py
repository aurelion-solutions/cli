"""Tests for al secrets create command."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from main import app

runner = CliRunner()


@patch("al.secrets.cli.httpx_client")
def test_secrets_create_invokes_post_endpoint(mock_client_class):
    """al secrets create invokes POST /secrets with correct payload."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app,
        [
            "secrets",
            "create",
            "--key",
            "github/token",
            "--provider",
            "file",
            "--namespace",
            "default",
            "--value",
            "secret123",
        ],
    )

    assert result.exit_code == 0
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args
    assert "/api/v0/secrets" in str(call_args[0][0])
    assert call_args[1]["json"] == {
        "key": "github/token",
        "provider": "file",
        "namespace": "default",
        "value": "secret123",
    }
    assert "Secret created" in result.output
