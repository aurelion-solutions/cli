"""Tests for al employee-records attributes command."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from main import app

runner = CliRunner()


@patch("al.employee_records.cli.httpx_client")
def test_employee_records_attributes_invokes_get_endpoint(
    mock_client_class,
) -> None:
    """al employee-records attributes invokes GET /api/v0/employee-records/{id}/attributes."""
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {
            "id": "770e8400-e29b-41d4-a716-446655440002",
            "employee_record_id": "550e8400-e29b-41d4-a716-446655440000",
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
        app,
        [
            "employee-records",
            "attributes",
            "550e8400-e29b-41d4-a716-446655440000",
        ],
    )

    assert result.exit_code == 0
    mock_client.get.assert_called_once()
    call_args = mock_client.get.call_args
    assert (
        "/api/v0/employee-records/550e8400-e29b-41d4-a716-446655440000/attributes"
        in str(call_args[0][0])
    )
