"""Tests for al logs read command."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from main import app

runner = CliRunner()


@patch("al.logs.cli.httpx_client")
def test_logs_read_outputs_recent_records(mock_client_class):
    """al logs read outputs recent log records for file provider."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "event_type": "test",
            "level": "info",
            "message": "hello",
            "component": "test",
        },
    ]
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["logs", "read"])

    assert result.exit_code == 0
    mock_client.get.assert_called_once()
    call_args = mock_client.get.call_args
    assert "/api/v0/logs" in str(call_args[0][0])
    assert "hello" in result.output
    assert "test" in result.output


@patch("al.logs.cli.httpx_client")
def test_logs_read_passes_limit_param(mock_client_class):
    """al logs read passes --limit to API."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = []
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["logs", "read", "--limit", "50"])

    assert result.exit_code == 0
    call_kwargs = mock_client.get.call_args[1]
    assert call_kwargs["params"] == {"limit": 50}


@patch("al.logs.cli.httpx_client")
def test_logs_read_fails_clearly_for_stub_provider(mock_client_class):
    """al logs read fails clearly when provider read is stub (501)."""
    mock_response = MagicMock()
    mock_response.status_code = 501
    mock_response.text = "Log read not implemented for provider 'elk'"
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["logs", "read"])

    assert result.exit_code == 1
    assert (
        "501" in result.output
        or "not supported" in result.output.lower()
        or "not implemented" in result.output.lower()
    )
