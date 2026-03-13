"""Tests for al app list command."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from main import app

runner = CliRunner()


@patch("al.app.cli.httpx_client")
def test_app_list_invokes_get_endpoint(mock_client_class):
    """al app list invokes GET /applications."""
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "my-app",
            "config": {},
            "required_connector_tags": [],
            "is_active": True,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z",
        },
    ]
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["app", "list"])

    assert result.exit_code == 0
    mock_client.get.assert_called_once()
    call_args = mock_client.get.call_args
    assert "/api/v0/applications" in str(call_args[0][0])
    assert "550e8400-e29b-41d4-a716-446655440000" in result.output
    assert "my-app" in result.output
