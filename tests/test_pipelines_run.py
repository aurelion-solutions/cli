"""Tests for al pipelines run command."""

import json
from unittest.mock import MagicMock, patch

import httpx
from typer.testing import CliRunner

from conftest import make_mock_http_client
from main import app

runner = CliRunner()

PIPELINE_NAME = "application_sync"
RUN_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

RUN_CREATED_201 = {
    "pipeline_run_id": RUN_ID,
    "pipeline_name": PIPELINE_NAME,
    "pipeline_version": 1,
    "status": "pending",
    "created": True,
}

RUN_CREATED_200 = {
    "pipeline_run_id": RUN_ID,
    "pipeline_name": PIPELINE_NAME,
    "pipeline_version": 1,
    "status": "pending",
    "created": False,
}


@patch("al.pipelines.cli.httpx_client")
def test_run_happy_path_201_text(mock_client_class) -> None:
    """201 response → exit 0, stdout contains run_id and created=True."""
    mock_client_class.return_value = make_mock_http_client(
        "post", return_value=RUN_CREATED_201, status_code=201
    )

    result = runner.invoke(app, ["pipelines", "run", PIPELINE_NAME])

    assert result.exit_code == 0
    assert f"pipeline_run_id={RUN_ID}" in result.output
    assert "created=True" in result.output


@patch("al.pipelines.cli.httpx_client")
def test_run_happy_path_200_idempotent_text(mock_client_class) -> None:
    """200 response (idempotent dedupe) → exit 0, stdout contains created=False."""
    mock_client_class.return_value = make_mock_http_client(
        "post", return_value=RUN_CREATED_200, status_code=200
    )

    result = runner.invoke(app, ["pipelines", "run", PIPELINE_NAME])

    assert result.exit_code == 0
    assert "created=False" in result.output


@patch("al.pipelines.cli.httpx_client")
def test_run_with_args_and_version_sends_correct_body(mock_client_class) -> None:
    """--args and --version are forwarded verbatim in the POST body."""
    mock_client = make_mock_http_client(
        "post", return_value=RUN_CREATED_201, status_code=201
    )
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app,
        ["pipelines", "run", "p", "--args", '{"foo": 1}', "--version", "3"],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.post.call_args
    sent_body = call_kwargs[1]["json"]
    assert sent_body == {
        "pipeline_name": "p",
        "pipeline_version": 3,
        "args": {"foo": 1},
    }


@patch("al.pipelines.cli.httpx_client")
def test_run_omits_version_when_not_passed(mock_client_class) -> None:
    """When --version is not supplied, pipeline_version must not appear in body."""
    mock_client = make_mock_http_client(
        "post", return_value=RUN_CREATED_201, status_code=201
    )
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["pipelines", "run", "p"])

    assert result.exit_code == 0
    call_kwargs = mock_client.post.call_args
    sent_body = call_kwargs[1]["json"]
    assert "pipeline_version" not in sent_body


def test_run_invalid_args_json() -> None:
    """Non-JSON --args → exit 2 with 'Invalid --args JSON' in stderr."""
    result = runner.invoke(
        app, ["pipelines", "run", PIPELINE_NAME, "--args", "not-json"]
    )

    assert result.exit_code == 2
    combined = result.output + (result.stderr or "")
    assert "Invalid --args JSON" in combined


def test_run_args_not_object() -> None:
    """Non-dict JSON (e.g. list) → exit 2 with 'Invalid --args JSON' in stderr."""
    result = runner.invoke(app, ["pipelines", "run", PIPELINE_NAME, "--args", "[1,2]"])

    assert result.exit_code == 2
    combined = result.output + (result.stderr or "")
    assert "Invalid --args JSON" in combined


@patch("al.pipelines.cli.httpx_client")
def test_run_404(mock_client_class) -> None:
    """404 from API → exit 1 with 'not loaded' in output."""
    error_body = {"detail": "Pipeline not found"}
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

    result = runner.invoke(app, ["pipelines", "run", PIPELINE_NAME])

    assert result.exit_code == 1
    combined = result.output + (result.stderr or "")
    assert "not loaded" in combined


@patch("al.pipelines.cli.httpx_client")
def test_run_422_with_detail(mock_client_class) -> None:
    """422 with detail → exit 1 with 'Invalid args' in output."""
    error_body = {"detail": "args.application_id: field required"}
    mock_response = MagicMock()
    mock_response.status_code = 422
    mock_response.text = json.dumps(error_body)
    mock_response.json.return_value = error_body
    exc = httpx.HTTPStatusError(
        message="HTTP 422", request=MagicMock(), response=mock_response
    )
    mock_client_class.return_value = make_mock_http_client(
        "post", return_value=error_body, status_code=422, raise_for_status_exc=exc
    )

    result = runner.invoke(app, ["pipelines", "run", PIPELINE_NAME])

    assert result.exit_code == 1
    combined = result.output + (result.stderr or "")
    assert "Invalid args" in combined


@patch("al.pipelines.cli.httpx_client")
def test_run_422_without_detail_generic_error(mock_client_class) -> None:
    """422 without 'detail' key → falls through to generic API error (exit 1)."""
    error_body = {"errors": ["bad field"]}
    mock_response = MagicMock()
    mock_response.status_code = 422
    mock_response.text = json.dumps(error_body)
    mock_response.json.return_value = error_body
    exc = httpx.HTTPStatusError(
        message="HTTP 422", request=MagicMock(), response=mock_response
    )
    mock_client_class.return_value = make_mock_http_client(
        "post", return_value=error_body, status_code=422, raise_for_status_exc=exc
    )

    result = runner.invoke(app, ["pipelines", "run", PIPELINE_NAME])

    assert result.exit_code == 1
    combined = result.output + (result.stderr or "")
    assert "API error 422" in combined


@patch("al.pipelines.cli.httpx_client")
def test_run_connection_error(mock_client_class) -> None:
    """ConnectError → exit 1."""
    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.post.side_effect = httpx.ConnectError("refused")
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["pipelines", "run", PIPELINE_NAME])

    assert result.exit_code == 1


@patch("al.pipelines.cli.httpx_client")
def test_run_timeout_error(mock_client_class) -> None:
    """TimeoutException → exit 1."""
    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.post.side_effect = httpx.TimeoutException("timed out")
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["pipelines", "run", PIPELINE_NAME])

    assert result.exit_code == 1
