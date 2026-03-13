"""Tests for al employees list command."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from main import app

runner = CliRunner()


@patch("al.employees.cli.httpx_client")
def test_employees_list_invokes_get_endpoint(mock_client_class) -> None:
    """al employees list invokes GET /api/v0/employees."""
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "person_id": "660e8400-e29b-41d4-a716-446655440001",
            "is_locked": False,
            "description": "Alice",
        },
    ]
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["employees", "list"])

    assert result.exit_code == 0
    mock_client.get.assert_called_once()
    call_args = mock_client.get.call_args
    assert "/api/v0/employees" in str(call_args[0][0])
