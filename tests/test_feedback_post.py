"""Tests for al feedback post command."""

import json
from unittest.mock import MagicMock, patch

import httpx
from typer.testing import CliRunner

from main import app

runner = CliRunner()

SUBJECT_UUID = "11111111-1111-1111-1111-111111111111"
FEEDBACK_RESPONSE = {
    "id": 99,
    "kind": "false_positive",
    "message": "This is not a real violation",
    "rule_id": 1,
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


@patch("al.feedback.cli.httpx_client")
def test_feedback_post_with_rule(mock_client_class) -> None:
    mock_client = _make_mock_client(201, FEEDBACK_RESPONSE)
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app,
        [
            "feedback",
            "post",
            "--kind",
            "false_positive",
            "--message",
            "This is not a real violation",
            "--rule",
            "1",
        ],
    )

    assert result.exit_code == 0
    call_url = mock_client.post.call_args[0][0]
    assert "/api/v0/feedbacks" in call_url
    call_body = mock_client.post.call_args[1]["json"]
    assert call_body["kind"] == "false_positive"
    assert call_body["message"] == "This is not a real violation"
    assert call_body["rule_id"] == 1
    assert "payload" not in call_body


@patch("al.feedback.cli.httpx_client")
def test_feedback_post_with_payload_file(mock_client_class, tmp_path) -> None:
    payload = {"custom_key": "custom_value", "count": 42}
    payload_file = tmp_path / "payload.json"
    payload_file.write_text(json.dumps(payload))

    mock_client = _make_mock_client(201, FEEDBACK_RESPONSE)
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app,
        [
            "feedback",
            "post",
            "--kind",
            "accepted_risk",
            "--message",
            "Accepted by management",
            "--finding",
            "5",
            "--payload-file",
            str(payload_file),
        ],
    )

    assert result.exit_code == 0
    call_body = mock_client.post.call_args[1]["json"]
    assert call_body["payload"] == payload
    assert call_body["finding_id"] == 5


@patch("al.feedback.cli.httpx_client")
def test_feedback_post_missing_all_targets(mock_client_class) -> None:
    result = runner.invoke(
        app,
        [
            "feedback",
            "post",
            "--kind",
            "false_positive",
            "--message",
            "Some message",
        ],
    )

    assert result.exit_code == 2
    assert (
        "rule" in result.output.lower()
        or "mapping" in result.output.lower()
        or "finding" in result.output.lower()
    )
    mock_client_class.assert_not_called()


@patch("al.feedback.cli.httpx_client")
def test_feedback_post_malformed_payload_file(mock_client_class, tmp_path) -> None:
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{not valid json")

    result = runner.invoke(
        app,
        [
            "feedback",
            "post",
            "--kind",
            "false_positive",
            "--message",
            "Test",
            "--rule",
            "1",
            "--payload-file",
            str(bad_file),
        ],
    )

    assert result.exit_code == 2
    mock_client_class.assert_not_called()


@patch("al.feedback.cli.httpx_client")
def test_feedback_post_422_validation_error(mock_client_class) -> None:
    error_body = {"detail": [{"loc": ["body", "message"], "msg": "min length 1"}]}
    mock_client = _make_mock_client(422, error_body)
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app,
        [
            "feedback",
            "post",
            "--kind",
            "false_positive",
            "--message",
            "",
            "--rule",
            "1",
        ],
    )

    assert result.exit_code == 1
    assert "Validation error:" in result.output


@patch("al.feedback.cli.httpx_client")
def test_feedback_post_with_mapping_and_subject(mock_client_class) -> None:
    mock_client = _make_mock_client(201, FEEDBACK_RESPONSE)
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app,
        [
            "feedback",
            "post",
            "--kind",
            "needs_mapping_fix",
            "--message",
            "Mapping is incorrect",
            "--mapping",
            "7",
            "--subject",
            SUBJECT_UUID,
        ],
    )

    assert result.exit_code == 0
    call_body = mock_client.post.call_args[1]["json"]
    assert call_body["capability_mapping_id"] == 7
    assert call_body["subject_id"] == SUBJECT_UUID
