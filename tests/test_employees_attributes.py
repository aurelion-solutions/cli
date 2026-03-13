"""Tests for al employees attributes command."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from main import app

runner = CliRunner()


@patch("al.employees.cli.httpx_client")
def test_employees_attributes_invokes_get_endpoint(mock_client_class) -> None:
    """al employees attributes invokes GET /api/v0/employees/{id}/attributes."""
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {
            "id": "770e8400-e29b-41d4-a716-446655440002",
            "employee_id": "550e8400-e29b-41d4-a716-446655440000",
            "key": "title",
            "value": "Engineer",
        },
    ]
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app, ["employees", "attributes", "550e8400-e29b-41d4-a716-446655440000"]
    )

    assert result.exit_code == 0
    mock_client.get.assert_called_once()
    call_args = mock_client.get.call_args
    assert "/api/v0/employees/550e8400-e29b-41d4-a716-446655440000/attributes" in str(
        call_args[0][0]
    )
