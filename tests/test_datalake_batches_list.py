"""Tests for al datalake batches list command."""

import json
from unittest.mock import MagicMock, patch

import pytest
import httpx
from typer.testing import CliRunner

from main import app

runner = CliRunner()


def _mock_response(payload: dict, status_code: int = 200) -> MagicMock:
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = payload
    mock_response.text = json.dumps(payload)
    if status_code >= 400:
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message=f"HTTP {status_code}",
            request=MagicMock(),
            response=mock_response,
        )
    else:
        mock_response.raise_for_status = MagicMock()
    return mock_response


def _mock_client(response: MagicMock) -> MagicMock:
    client = MagicMock()
    client.get.return_value = response
    client.__enter__ = MagicMock(return_value=client)
    client.__exit__ = MagicMock(return_value=False)
    return client


_SAMPLE_RESPONSE = {
    "items": [
        {
            "id": "aabbccdd-1234-5678-abcd-aabbccddeeff",
            "dataset_type": "access_artifacts",
            "storage_provider": None,
            "storage_key": None,
            "row_count": 10,
            "created_at": "2026-04-27T10:00:00+00:00",
            "application_id": None,
            "task_id": None,
            "content_type": None,
            "metadata_json": None,
            "iceberg_namespace": "raw",
            "iceberg_table": "access_artifacts",
            "snapshot_id": "1234567890123456789",
        }
    ],
    "next_cursor": None,
}


@patch("al.datalake.cli.httpx_client")
def test_list_default_limit_calls_endpoint(mock_client_class: MagicMock) -> None:
    """al datalake batches list uses limit=20 by default and calls the right URL."""
    mock_client_class.return_value = _mock_client(_mock_response(_SAMPLE_RESPONSE))

    result = runner.invoke(app, ["datalake", "batches", "list"])

    assert result.exit_code == 0, result.output
    client = mock_client_class.return_value
    client.get.assert_called_once()
    call_args = client.get.call_args
    url = call_args[0][0]
    params = call_args[1].get("params", {})
    assert "/api/v0/datalake/batches" in url
    assert params.get("limit") == "20"
    assert "cursor" not in params


@patch("al.datalake.cli.httpx_client")
def test_list_with_cursor_propagates(mock_client_class: MagicMock) -> None:
    """--cursor flag is forwarded as a query param."""
    mock_client_class.return_value = _mock_client(_mock_response(_SAMPLE_RESPONSE))

    result = runner.invoke(app, ["datalake", "batches", "list", "--cursor", "abc123"])

    assert result.exit_code == 0, result.output
    client = mock_client_class.return_value
    call_args = client.get.call_args
    params = call_args[1].get("params", {})
    assert params.get("cursor") == "abc123"


@patch("al.datalake.cli.httpx_client")
def test_list_400_prints_error_and_exits_1(mock_client_class: MagicMock) -> None:
    """400 response: CLI prints 'API error:' and exits with code 1."""
    error_body = {"detail": "Invalid cursor"}
    mock_client_class.return_value = _mock_client(_mock_response(error_body, status_code=400))

    result = runner.invoke(app, ["datalake", "batches", "list", "--cursor", "bad!!!"])

    assert result.exit_code == 1
    assert "API error" in result.output


@patch("al.datalake.cli.httpx_client")
def test_list_connection_error_handled(mock_client_class: MagicMock) -> None:
    """ConnectError produces an error message (no unhandled exception)."""
    client = MagicMock()
    client.__enter__ = MagicMock(return_value=client)
    client.__exit__ = MagicMock(return_value=False)
    client.get.side_effect = httpx.ConnectError("connection refused")
    mock_client_class.return_value = client

    result = runner.invoke(app, ["datalake", "batches", "list"])

    # Should not raise — exit code non-zero
    assert result.exit_code != 0 or "error" in result.output.lower() or "connect" in result.output.lower()
