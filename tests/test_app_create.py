"""Tests for al app create command."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from main import app

runner = CliRunner()


@patch("al.app.cli.httpx_client")
def test_app_create_invokes_post_with_correct_payload(mock_client_class):
    """al app create invokes POST /applications with correct payload."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "my-app",
        "code": "my-app",
        "config": {"queue": "test-queue"},
        "required_connector_tags": [],
        "is_active": True,
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
    }
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app,
        [
            "app",
            "create",
            "--name",
            "my-app",
            "--code",
            "my-app",
            "--config",
            '{"queue": "test-queue"}',
        ],
    )

    assert result.exit_code == 0
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args
    assert "/api/v0/applications" in str(call_args[0][0])
    assert call_args[1]["json"] == {
        "name": "my-app",
        "code": "my-app",
        "config": {"queue": "test-queue"},
        "required_connector_tags": [],
        "is_active": True,
    }
    assert "Created application" in result.output
    assert "my-app" in result.output
