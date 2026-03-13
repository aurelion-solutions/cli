"""Tests for al datalake batches get command."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from main import app

runner = CliRunner()


@patch("al.datalake.cli.httpx_client")
def test_datalake_batches_get_invokes_get_endpoint(mock_client_class) -> None:
    """al datalake batches get invokes GET /api/v0/datalake/batches/{id}."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "storage_provider": "file",
        "dataset_type": "accounts",
        "row_count": 5,
    }
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app,
        ["datalake", "batches", "get", "550e8400-e29b-41d4-a716-446655440000"],
    )

    assert result.exit_code == 0
    mock_client.get.assert_called_once()
    call_args = mock_client.get.call_args
    assert "/api/v0/datalake/batches/550e8400-e29b-41d4-a716-446655440000" in str(
        call_args[0][0]
    )
