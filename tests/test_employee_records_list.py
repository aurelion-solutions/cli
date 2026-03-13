"""Tests for al employee-records list command."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from main import app

runner = CliRunner()


@patch("al.employee_records.cli.httpx_client")
def test_employee_records_list_invokes_get_endpoint(mock_client_class) -> None:
    """al employee-records list invokes GET /api/v0/employee-records."""
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "external_id": "rec-1",
            "application_id": "660e8400-e29b-41d4-a716-446655440001",
            "description": "Alice",
        },
    ]
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["employee-records", "list"])

    assert result.exit_code == 0
    mock_client.get.assert_called_once()
    call_args = mock_client.get.call_args
    assert "/api/v0/employee-records" in str(call_args[0][0])
