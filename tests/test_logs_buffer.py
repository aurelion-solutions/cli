"""Tests for al logs buffer command."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from main import app

runner = CliRunner()


@patch("al.logs.cli.httpx_client")
def test_logs_buffer_hits_log_buffer_endpoint(mock_client_class):
    """al logs buffer invokes GET /api/v0/log-buffer."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"event_type": "test", "correlation_id": "c1", "message": "hello"},
    ]
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["logs", "buffer", "--correlation-id", "trace-1"])

    assert result.exit_code == 0
    mock_client.get.assert_called_once()
    call_args = mock_client.get.call_args
    assert "/api/v0/log-buffer" in str(call_args[0][0])
    params = call_args[1]["params"]
    assert params["correlation_id"] == "trace-1"
    assert params["order"] == "desc"
    assert params["limit"] == 100
    assert "hello" in result.output


@patch("al.logs.cli.httpx_client")
def test_logs_buffer_passes_filters_and_order(mock_client_class):
    """al logs buffer forwards query params."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = []
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app,
        [
            "logs",
            "buffer",
            "--event-type",
            "connector.command.received",
            "--order",
            "asc",
            "--limit",
            "50",
            "--level",
            "info",
        ],
    )

    assert result.exit_code == 0
    params = mock_client.get.call_args[1]["params"]
    assert params["event_type"] == "connector.command.received"
    assert params["order"] == "asc"
    assert params["limit"] == 50
    assert params["level"] == "info"


@patch("al.logs.cli.httpx_client")
def test_logs_buffer_exits_on_api_validation_error(mock_client_class):
    """al logs buffer exits 1 on 422 from API."""
    mock_response = MagicMock()
    mock_response.status_code = 422
    mock_response.text = "validation error"
    mock_response.json.return_value = {"detail": [{"type": "literal_error"}]}
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app, ["logs", "buffer", "--correlation-id", "x", "--order", "invalid"]
    )

    assert result.exit_code == 1
    assert "422" in result.output or "failed" in result.output.lower()
