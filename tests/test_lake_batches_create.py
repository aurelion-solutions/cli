"""Tests for al datalake batches create command."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from main import app

runner = CliRunner()


@patch("al.datalake.cli.httpx_client")
def test_datalake_batches_create_invokes_post_with_correct_payload(
    mock_client_class,
) -> None:
    """al datalake batches create invokes POST /api/v0/datalake/batches with correct payload."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "storage_provider": "file",
        "dataset_type": "accounts",
        "storage_key": "accounts/uuid",
        "row_count": 1,
        "created_at": "2025-01-01T00:00:00Z",
    }
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app,
        [
            "datalake",
            "batches",
            "create",
            "--storage-provider",
            "file",
            "--dataset-type",
            "accounts",
            "--records",
            '[{"id":"1"}]',
        ],
    )

    assert result.exit_code == 0
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args
    assert "/api/v0/datalake/batches" in str(call_args[0][0])
    assert call_args[1]["json"]["storage_provider"] == "file"
    assert call_args[1]["json"]["dataset_type"] == "accounts"
    assert call_args[1]["json"]["records"] == [{"id": "1"}]
    assert "Created lake batch" in result.output
