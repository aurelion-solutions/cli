"""Tests for al app reconcile run command."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from main import app

runner = CliRunner()


@patch("al.app.cli.httpx_client")
def test_app_reconcile_run_invokes_api_and_prints_result(mock_client_class):
    """al app reconcile run invokes API and prints result."""
    mock_response = MagicMock()
    mock_response.status_code = 202
    mock_response.json.return_value = {
        "application_id": "550e8400-e29b-41d4-a716-446655440000",
        "correlation_id": "corr-test-1",
    }
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app,
        ["app", "reconcile", "run", "--app-id", "550e8400-e29b-41d4-a716-446655440000"],
    )

    assert result.exit_code == 0
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args
    assert "/api/v0/applications/550e8400-e29b-41d4-a716-446655440000/reconcile" in str(
        call_args[0][0]
    )
    assert "Reconciliation started" in result.output
    assert "correlation_id" in result.output
