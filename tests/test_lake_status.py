"""Tests for al lake status command."""

import json
from unittest.mock import MagicMock, patch

import httpx
from typer.testing import CliRunner

from main import app

runner = CliRunner()


def _make_mock_client(return_value):
    mock_response = MagicMock()
    mock_response.json.return_value = return_value
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    return mock_client


@patch("al.lake.api.httpx_client")
def test_status_invokes_get_status_endpoint(mock_client_class) -> None:
    """al lake status calls GET /api/v0/lake/status."""
    mock_client = _make_mock_client({"catalog_uri": "s3://bucket", "tables": []})
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["lake", "status"])

    assert result.exit_code == 0
    mock_client.get.assert_called_once()
    call_args = mock_client.get.call_args
    assert "/api/v0/lake/status" in str(call_args[0][0])


@patch("al.lake.api.httpx_client")
def test_status_prints_response_as_indented_json(mock_client_class) -> None:
    """Output is the mocked response body as indented JSON."""
    body = {
        "catalog_uri": "s3://my-bucket/catalog",
        "warehouse_uri": "s3://my-bucket/warehouse",
        "tables": [
            {
                "namespace": "raw",
                "table": "access_artifacts",
                "snapshot_count": 3,
                "current_snapshot_id": 42,
            }
        ],
    }
    mock_client = _make_mock_client(body)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["lake", "status"])

    assert result.exit_code == 0
    assert json.loads(result.output) == body


@patch("al.lake.api.httpx_client")
def test_status_connection_refused_exits_1(mock_client_class) -> None:
    """ConnectError causes exit 1 and mentions Connection refused."""
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.ConnectError("refused")
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["lake", "status"])

    assert result.exit_code == 1
    assert "Connection refused" in result.output


@patch("al.lake.api.httpx_client")
def test_status_timeout_exits_1(mock_client_class) -> None:
    """TimeoutException causes exit 1 and mentions timed out."""
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.TimeoutException("timeout")
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["lake", "status"])

    assert result.exit_code == 1
    assert "timed out" in result.output.lower()
