"""Tests for al datalake batches data command."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from main import app

runner = CliRunner()


@patch("al.datalake.cli.httpx_client")
def test_datalake_batches_data_invokes_get_data_endpoint(mock_client_class) -> None:
    """al datalake batches data invokes GET /api/v0/datalake/batches/{id}/data."""
    mock_response = MagicMock()
    mock_response.json.return_value = [{"id": "1"}, {"id": "2"}]
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app,
        ["datalake", "batches", "data", "550e8400-e29b-41d4-a716-446655440000"],
    )

    assert result.exit_code == 0
    mock_client.get.assert_called_once()
    call_args = mock_client.get.call_args
    assert "/api/v0/datalake/batches/550e8400-e29b-41d4-a716-446655440000/data" in str(
        call_args[0][0]
    )
    assert "id" in result.output or "1" in result.output
