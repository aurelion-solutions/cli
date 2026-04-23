"""Tests for al reconciliation run command."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from main import app

runner = CliRunner()


@patch("al.reconciliation.cli.httpx_client")
def test_reconciliation_run_happy_path(mock_client_class):
    """al reconciliation run returns summary and exits 0 on HTTP 200."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "application_id": "550e8400-e29b-41d4-a716-446655440000",
        "started_at": "2026-04-23T10:00:00+00:00",
        "finished_at": "2026-04-23T10:00:01+00:00",
        "artifacts_ingested": 5,
        "facts_created": 3,
        "facts_updated": 1,
        "facts_revoked": 0,
        "artifacts_unhandled": 1,
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
            "reconciliation",
            "run",
            "--application-id",
            "550e8400-e29b-41d4-a716-446655440000",
        ],
    )

    assert result.exit_code == 0
    mock_client.post.assert_called_once()
    call_url = mock_client.post.call_args[0][0]
    assert "/api/v0/reconciliation/runs" in call_url

    assert "facts_created" in result.output
    assert "artifacts_ingested" in result.output


@patch("al.reconciliation.cli.httpx_client")
def test_reconciliation_run_404(mock_client_class):
    """al reconciliation run exits non-zero on HTTP 404."""
    import httpx

    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = '{"detail": "Application not found"}'

    http_error = httpx.HTTPStatusError(
        "404",
        request=MagicMock(),
        response=mock_response,
    )
    mock_response.raise_for_status.side_effect = http_error

    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app,
        [
            "reconciliation",
            "run",
            "--application-id",
            "00000000-0000-0000-0000-000000000001",
        ],
    )

    assert result.exit_code != 0
    assert "not found" in result.output.lower() or "not found" in (result.stderr or "").lower()
