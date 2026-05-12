"""Tests for al pipelines runs cancel command."""

import json
from unittest.mock import MagicMock, patch

import httpx
from typer.testing import CliRunner

from conftest import make_mock_http_client
from main import app

runner = CliRunner()

RUN_ID = "cccccccc-cccc-cccc-cccc-cccccccccccc"

CANCEL_CANCELLED = {"run_id": RUN_ID, "status": "cancelled"}
CANCEL_CANCELLING = {"run_id": RUN_ID, "status": "cancelling"}


@patch("al.pipelines.cli.httpx_client")
def test_cancel_happy_cancelled_text(mock_client_class) -> None:
    """200 status=cancelled → exit 0, output contains run_id and status."""
    mock_client_class.return_value = make_mock_http_client(
        "post", return_value=CANCEL_CANCELLED
    )

    result = runner.invoke(app, ["pipelines", "runs", "cancel", RUN_ID])

    assert result.exit_code == 0
    assert f"run_id={RUN_ID}" in result.output
    assert "cancelled" in result.output


@patch("al.pipelines.cli.httpx_client")
def test_cancel_happy_cancelling_text(mock_client_class) -> None:
    """200 status=cancelling → exit 0 (async cancel accepted)."""
    mock_client_class.return_value = make_mock_http_client(
        "post", return_value=CANCEL_CANCELLING
    )

    result = runner.invoke(app, ["pipelines", "runs", "cancel", RUN_ID])

    assert result.exit_code == 0
    assert "cancelling" in result.output


@patch("al.pipelines.cli.httpx_client")
def test_cancel_json(mock_client_class) -> None:
    """--format json round-trip."""
    mock_client_class.return_value = make_mock_http_client(
        "post", return_value=CANCEL_CANCELLED
    )

    result = runner.invoke(
        app, ["pipelines", "runs", "cancel", RUN_ID, "--format", "json"]
    )

    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["run_id"] == RUN_ID
    assert parsed["status"] == "cancelled"


@patch("al.pipelines.cli.httpx_client")
def test_cancel_404(mock_client_class) -> None:
    """404 → exit 1 with 'not found' in output."""
    error_body = {"detail": "Pipeline run not found"}
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = json.dumps(error_body)
    mock_response.json.return_value = error_body
    exc = httpx.HTTPStatusError(
        message="HTTP 404", request=MagicMock(), response=mock_response
    )
    mock_client_class.return_value = make_mock_http_client(
        "post", return_value=error_body, status_code=404, raise_for_status_exc=exc
    )

    result = runner.invoke(app, ["pipelines", "runs", "cancel", RUN_ID])

    assert result.exit_code == 1
    combined = result.output + (result.stderr or "")
    assert "not found" in combined.lower()


@patch("al.pipelines.cli.httpx_client")
def test_cancel_409_already_cancelling(mock_client_class) -> None:
    """409 → exit 1 with kernel detail surfaced verbatim."""
    kernel_detail = "Pipeline run is already cancelling"
    error_body = {"detail": kernel_detail}
    mock_response = MagicMock()
    mock_response.status_code = 409
    mock_response.text = json.dumps(error_body)
    mock_response.json.return_value = error_body
    exc = httpx.HTTPStatusError(
        message="HTTP 409", request=MagicMock(), response=mock_response
    )
    mock_client_class.return_value = make_mock_http_client(
        "post", return_value=error_body, status_code=409, raise_for_status_exc=exc
    )

    result = runner.invoke(app, ["pipelines", "runs", "cancel", RUN_ID])

    assert result.exit_code == 1
    combined = result.output + (result.stderr or "")
    assert kernel_detail in combined


@patch("al.pipelines.cli.httpx_client")
def test_cancel_connection_error(mock_client_class) -> None:
    """ConnectError → exit 1."""
    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.post.side_effect = httpx.ConnectError("refused")
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["pipelines", "runs", "cancel", RUN_ID])

    assert result.exit_code == 1
