"""Tests for al app connectors list command."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from main import app

runner = CliRunner()


@patch("al.connectors.cli.httpx_client")
def test_connectors_list_invokes_get_endpoint(mock_client_class):
    """al app connectors list invokes GET /connector-instances."""
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "instance_id": "runtime-a",
            "tags": ["jira"],
            "is_online": True,
            "last_seen_at": "2025-01-01T00:00:00Z",
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

    result = runner.invoke(app, ["app", "connectors", "list"])

    assert result.exit_code == 0
    mock_client.get.assert_called_once()
    call_args = mock_client.get.call_args
    assert "/api/v0/connector-instances" in str(call_args[0][0])
    assert "runtime-a" in result.output
