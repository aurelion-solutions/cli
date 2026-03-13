"""Tests for al nhi get command."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from main import app

runner = CliRunner()


@patch("al.nhi.cli.httpx_client")
def test_nhi_get_invokes_get_endpoint(mock_client_class) -> None:
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "external_id": "nhi-1",
        "name": "Bot",
        "kind": "bot",
        "description": None,
        "is_locked": False,
        "owner_employee_id": None,
        "application_id": None,
    }
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app,
        ["nhi", "get", "550e8400-e29b-41d4-a716-446655440000"],
    )

    assert result.exit_code == 0
    assert "/api/v0/nhi/550e8400-e29b-41d4-a716-446655440000" in str(
        mock_client.get.call_args[0][0]
    )
