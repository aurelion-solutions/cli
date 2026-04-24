"""Tests for al sod what-if command."""

import json
from unittest.mock import MagicMock, patch

import httpx
from typer.testing import CliRunner

from main import app

runner = CliRunner()

SUBJECT_UUID = "11111111-1111-1111-1111-111111111111"
APP_UUID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
VIOLATIONS_RESPONSE = [
    {
        "rule_id": 1,
        "rule_code": "FIN-001",
        "severity": "high",
        "is_mitigated": False,
    }
]


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


@patch("al.sod.cli.httpx_client")
def test_what_if_two_overrides(mock_client_class) -> None:
    mock_client = _make_mock_client(200, VIOLATIONS_RESPONSE)
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app,
        [
            "sod",
            "what-if",
            SUBJECT_UUID,
            "--override",
            f"1:2:some_scope:{APP_UUID}",
            "--override",
            f"3:4:other_scope:{APP_UUID}",
        ],
    )

    assert result.exit_code == 0
    call_body = mock_client.post.call_args[1]["json"]
    assert call_body["subject_id"] == SUBJECT_UUID
    overrides = call_body["capability_overrides"]
    assert len(overrides) == 2
    assert overrides[0]["capability_id"] == 1
    assert overrides[0]["scope_key_id"] == 2
    assert overrides[0]["scope_value"] == "some_scope"
    assert overrides[0]["application_id"] == APP_UUID
    assert overrides[1]["capability_id"] == 3
    assert overrides[1]["scope_key_id"] == 4
    assert overrides[1]["scope_value"] == "other_scope"


@patch("al.sod.cli.httpx_client")
def test_what_if_null_scope_value(mock_client_class) -> None:
    mock_client = _make_mock_client(200, VIOLATIONS_RESPONSE)
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app,
        [
            "sod",
            "what-if",
            SUBJECT_UUID,
            "--override",
            f"1:2:null:{APP_UUID}",
        ],
    )

    assert result.exit_code == 0
    call_body = mock_client.post.call_args[1]["json"]
    assert call_body["capability_overrides"][0]["scope_value"] is None


@patch("al.sod.cli.httpx_client")
def test_what_if_null_scope_value_case_insensitive(mock_client_class) -> None:
    mock_client = _make_mock_client(200, VIOLATIONS_RESPONSE)
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app,
        [
            "sod",
            "what-if",
            SUBJECT_UUID,
            "--override",
            f"1:2:NULL:{APP_UUID}",
        ],
    )

    assert result.exit_code == 0
    call_body = mock_client.post.call_args[1]["json"]
    assert call_body["capability_overrides"][0]["scope_value"] is None


@patch("al.sod.cli.httpx_client")
def test_what_if_malformed_override_not_enough_parts(mock_client_class) -> None:
    result = runner.invoke(
        app,
        [
            "sod",
            "what-if",
            SUBJECT_UUID,
            "--override",
            "not_a_tuple",
        ],
    )

    assert result.exit_code == 2
    mock_client_class.assert_not_called()


@patch("al.sod.cli.httpx_client")
def test_what_if_malformed_override_non_int_capability_id(mock_client_class) -> None:
    result = runner.invoke(
        app,
        [
            "sod",
            "what-if",
            SUBJECT_UUID,
            "--override",
            f"abc:2:scope:{APP_UUID}",
        ],
    )

    assert result.exit_code == 2
    mock_client_class.assert_not_called()


@patch("al.sod.cli.httpx_client")
def test_what_if_malformed_override_invalid_uuid(mock_client_class) -> None:
    result = runner.invoke(
        app,
        [
            "sod",
            "what-if",
            SUBJECT_UUID,
            "--override",
            "1:2:scope:not-a-uuid",
        ],
    )

    assert result.exit_code == 2
    mock_client_class.assert_not_called()


@patch("al.sod.cli.httpx_client")
def test_what_if_empty_override_list(mock_client_class) -> None:
    mock_client = _make_mock_client(200, [])
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["sod", "what-if", SUBJECT_UUID])

    assert result.exit_code == 0
    call_body = mock_client.post.call_args[1]["json"]
    assert call_body["capability_overrides"] == []


@patch("al.sod.cli.httpx_client")
def test_what_if_422_validation_error(mock_client_class) -> None:
    error_body = {"detail": [{"loc": ["body", "subject_id"], "msg": "field required"}]}
    mock_client = _make_mock_client(422, error_body)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["sod", "what-if", SUBJECT_UUID])

    assert result.exit_code == 1
    assert "Validation error:" in result.output
