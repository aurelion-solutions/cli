"""Tests for al inventory accounts get command."""

import uuid
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from main import app

runner = CliRunner()


@patch("al.inventory.cli.httpx_client")
def test_accounts_get_invokes_get_by_id_endpoint(mock_client_class) -> None:
    """al inventory accounts get <id> invokes GET /api/v0/accounts/<id>."""
    account_id = str(uuid.uuid4())
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "id": account_id,
        "username": "testuser",
        "status": "active",
    }
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["inventory", "accounts", "get", account_id])

    assert result.exit_code == 0
    mock_client.get.assert_called_once()
    call_args = mock_client.get.call_args
    assert f"/api/v0/accounts/{account_id}" in str(call_args[0][0])
