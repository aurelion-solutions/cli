"""Tests for al app delete command."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from main import app

runner = CliRunner()


@patch("al.app.cli.httpx_client")
def test_app_delete_invokes_delete_endpoint(mock_client_class):
    """al app delete invokes DELETE /applications/{id}."""
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.delete.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app,
        ["app", "delete", "--app-id", "550e8400-e29b-41d4-a716-446655440000"],
    )

    assert result.exit_code == 0
    mock_client.delete.assert_called_once()
    call_args = mock_client.delete.call_args
    assert "/api/v0/applications/550e8400-e29b-41d4-a716-446655440000" in str(
        call_args[0][0]
    )
    assert "Application deleted" in result.output
