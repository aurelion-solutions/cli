"""Tests for al inventory resources get command."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from main import app

runner = CliRunner()


@patch("al.inventory.cli.httpx_client")
def test_resources_get_invokes_get_endpoint(mock_client_class) -> None:
    """al inventory resources get <id> invokes GET /api/v0/resources/{id}."""
    resource_id = "11111111-1111-1111-1111-111111111111"
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "id": resource_id,
        "external_id": "ext-001",
        "kind": "table",
    }
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["inventory", "resources", "get", resource_id])

    assert result.exit_code == 0
    mock_client.get.assert_called_once()
    call_args = mock_client.get.call_args
    assert resource_id in str(call_args[0][0])
