"""Tests for al policy evaluate command."""

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest
from typer.testing import CliRunner

from main import app

runner = CliRunner()

FACTS_PAYLOAD = {
    "subject": {"id": "emp-1", "type": "employee"},
    "action": "read",
    "resource": {"type": "document", "id": "doc-42"},
}

DECISION_RESPONSE = {
    "decision": "allow",
    "matched_rule": "allow_read_documents",
}


def _make_mock_client(status_code: int, json_body: object) -> MagicMock:
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_body
    mock_response.text = json.dumps(json_body)

    if status_code >= 400:
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message=f"HTTP {status_code}",
            request=MagicMock(),
            response=mock_response,
        )
    else:
        mock_response.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    return mock_client


@patch("al.policy.cli.httpx_client")
def test_evaluate_from_file(mock_client_class, tmp_path) -> None:
    facts_file = tmp_path / "facts.json"
    facts_file.write_text(json.dumps(FACTS_PAYLOAD))

    mock_client = _make_mock_client(200, DECISION_RESPONSE)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["policy", "evaluate", "--file", str(facts_file)])

    assert result.exit_code == 0
    mock_client.post.assert_called_once()
    call_url = mock_client.post.call_args[0][0]
    assert "/api/v0/policy/evaluate" in call_url
    call_body = mock_client.post.call_args[1]["json"]
    assert call_body == FACTS_PAYLOAD
    assert "allow" in result.output


@patch("al.policy.cli.httpx_client")
def test_evaluate_from_stdin(mock_client_class) -> None:
    mock_client = _make_mock_client(200, DECISION_RESPONSE)
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app,
        ["policy", "evaluate"],
        input=json.dumps(FACTS_PAYLOAD),
    )

    assert result.exit_code == 0
    mock_client.post.assert_called_once()
    call_url = mock_client.post.call_args[0][0]
    assert "/api/v0/policy/evaluate" in call_url


@patch("al.policy.cli.httpx_client")
def test_evaluate_422_validation_error(mock_client_class) -> None:
    error_body = {"detail": [{"loc": ["body", "subject"], "msg": "field required"}]}
    mock_client = _make_mock_client(422, error_body)
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app,
        ["policy", "evaluate"],
        input=json.dumps(FACTS_PAYLOAD),
    )

    assert result.exit_code == 1
    assert "Validation error" in result.output


@patch("al.policy.cli.httpx_client")
def test_evaluate_connection_refused(mock_client_class) -> None:
    mock_client_class.side_effect = httpx.ConnectError("Connection refused")

    result = runner.invoke(
        app,
        ["policy", "evaluate"],
        input=json.dumps(FACTS_PAYLOAD),
    )

    assert result.exit_code == 1
    assert "Connection refused" in result.output


@patch("al.policy.cli.httpx_client")
def test_evaluate_timeout(mock_client_class) -> None:
    mock_client_class.side_effect = httpx.TimeoutException("Timeout")

    result = runner.invoke(
        app,
        ["policy", "evaluate"],
        input=json.dumps(FACTS_PAYLOAD),
    )

    assert result.exit_code == 1
    assert "timed out" in result.output


@pytest.mark.parametrize("bad_content", ["{not json}", "plain text", "[1, 2,"])
@patch("al.policy.cli.httpx_client")
def test_evaluate_invalid_json_file(mock_client_class, bad_content, tmp_path) -> None:
    bad_file = tmp_path / "bad.json"
    bad_file.write_text(bad_content)

    result = runner.invoke(app, ["policy", "evaluate", "--file", str(bad_file)])

    assert result.exit_code == 1
    assert "Invalid JSON" in result.output
    mock_client_class.assert_not_called()


@patch("al.policy.cli.httpx_client")
def test_evaluate_empty_stdin(mock_client_class) -> None:
    result = runner.invoke(app, ["policy", "evaluate"], input="")

    assert result.exit_code == 1
    assert "No input provided" in result.output
    mock_client_class.assert_not_called()
