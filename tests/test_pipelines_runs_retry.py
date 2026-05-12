"""Tests for al pipelines runs retry command."""

import json
from unittest.mock import MagicMock, patch

import httpx
from typer.testing import CliRunner

from conftest import make_mock_http_client
from main import app

runner = CliRunner()

RUN_ID = "dddddddd-dddd-dddd-dddd-dddddddddddd"
ORIGINAL_RUN_ID = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"
PIPELINE_NAME = "application_sync"

RETRY_RESPONSE = {
    "run_id": RUN_ID,
    "retry_of_run_id": ORIGINAL_RUN_ID,
    "status": "pending",
    "pipeline_name": PIPELINE_NAME,
    "pipeline_version": 1,
}


@patch("al.pipelines.cli.httpx_client")
def test_retry_happy_text(mock_client_class) -> None:
    """201 with all fields → stdout contains run_id, retry_of, status, pipeline, version."""
    mock_client_class.return_value = make_mock_http_client(
        "post", return_value=RETRY_RESPONSE, status_code=201
    )

    result = runner.invoke(app, ["pipelines", "runs", "retry", ORIGINAL_RUN_ID])

    assert result.exit_code == 0
    assert f"run_id={RUN_ID}" in result.output
    assert f"retry_of_run_id={ORIGINAL_RUN_ID}" in result.output
    assert "status=pending" in result.output
    assert f"pipeline={PIPELINE_NAME}" in result.output
    assert "version=1" in result.output


@patch("al.pipelines.cli.httpx_client")
def test_retry_json(mock_client_class) -> None:
    """--format json round-trip."""
    mock_client_class.return_value = make_mock_http_client(
        "post", return_value=RETRY_RESPONSE, status_code=201
    )

    result = runner.invoke(
        app, ["pipelines", "runs", "retry", ORIGINAL_RUN_ID, "--format", "json"]
    )

    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["run_id"] == RUN_ID
    assert parsed["retry_of_run_id"] == ORIGINAL_RUN_ID


@patch("al.pipelines.cli.httpx_client")
def test_retry_404(mock_client_class) -> None:
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

    result = runner.invoke(app, ["pipelines", "runs", "retry", ORIGINAL_RUN_ID])

    assert result.exit_code == 1
    combined = result.output + (result.stderr or "")
    assert "not found" in combined.lower()


@patch("al.pipelines.cli.httpx_client")
def test_retry_409_cancelling(mock_client_class) -> None:
    """409 cancelling → exit 1 with kernel detail verbatim."""
    kernel_detail = "Pipeline run is cancelling - wait for it to settle"
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

    result = runner.invoke(app, ["pipelines", "runs", "retry", ORIGINAL_RUN_ID])

    assert result.exit_code == 1
    combined = result.output + (result.stderr or "")
    assert kernel_detail in combined


@patch("al.pipelines.cli.httpx_client")
def test_retry_409_non_terminal(mock_client_class) -> None:
    """409 non-terminal → exit 1 with kernel detail verbatim."""
    kernel_detail = "Pipeline run is not in a terminal status: running"
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

    result = runner.invoke(app, ["pipelines", "runs", "retry", ORIGINAL_RUN_ID])

    assert result.exit_code == 1
    combined = result.output + (result.stderr or "")
    assert kernel_detail in combined


@patch("al.pipelines.cli.httpx_client")
def test_retry_connection_error(mock_client_class) -> None:
    """ConnectError → exit 1."""
    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.post.side_effect = httpx.ConnectError("refused")
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["pipelines", "runs", "retry", ORIGINAL_RUN_ID])

    assert result.exit_code == 1
