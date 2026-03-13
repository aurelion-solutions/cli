"""Tests for al inventory subject <id> command (two-call merge)."""

import json
from unittest.mock import MagicMock, patch

import httpx
from typer.testing import CliRunner

from main import app

runner = CliRunner()

SUBJECT_ID = "11111111-1111-1111-1111-111111111111"
SUBJECT_BODY = {"id": SUBJECT_ID, "kind": "employee", "status": "active"}
ATTRS_BODY = [{"key": "dept", "value": "eng"}]


def _make_ok_response(body):
    resp = MagicMock()
    resp.json.return_value = body
    resp.raise_for_status = MagicMock()
    return resp


def _make_error_response(status_code: int, text: str):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    error = httpx.HTTPStatusError(
        message=f"{status_code}",
        request=MagicMock(),
        response=MagicMock(text=text, status_code=status_code),
    )
    resp.raise_for_status = MagicMock(side_effect=error)
    return resp


@patch("al.inventory.cli.httpx_client")
def test_subject_get_calls_subject_and_attributes_endpoints(mock_client_class) -> None:
    """Two GET calls: /subjects/<id> then /subjects/<id>/attributes."""
    resp_subject = _make_ok_response(SUBJECT_BODY)
    resp_attrs = _make_ok_response(ATTRS_BODY)

    mock_client = MagicMock()
    mock_client.get.side_effect = [resp_subject, resp_attrs]
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["inventory", "subject", SUBJECT_ID])

    assert result.exit_code == 0
    assert mock_client.get.call_count == 2
    first_url = mock_client.get.call_args_list[0][0][0]
    second_url = mock_client.get.call_args_list[1][0][0]
    assert f"/api/v0/subjects/{SUBJECT_ID}" in first_url
    assert "/attributes" not in first_url
    assert f"/api/v0/subjects/{SUBJECT_ID}/attributes" in second_url


@patch("al.inventory.cli.httpx_client")
def test_subject_get_merges_subject_and_attributes_into_single_object(
    mock_client_class,
) -> None:
    """Output merges SubjectRead fields with attributes array."""
    resp_subject = _make_ok_response(SUBJECT_BODY)
    resp_attrs = _make_ok_response(ATTRS_BODY)

    mock_client = MagicMock()
    mock_client.get.side_effect = [resp_subject, resp_attrs]
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["inventory", "subject", SUBJECT_ID])

    assert result.exit_code == 0
    output = json.loads(result.output)
    expected = {**SUBJECT_BODY, "attributes": ATTRS_BODY}
    assert output == expected


@patch("al.inventory.cli.httpx_client")
def test_subject_get_404_on_subject_exits_1_without_calling_attributes(
    mock_client_class,
) -> None:
    """404 on first call → exit 1; attributes call is never made."""
    resp_subject = _make_error_response(404, '{"detail": "Subject not found"}')

    mock_client = MagicMock()
    mock_client.get.return_value = resp_subject
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["inventory", "subject", SUBJECT_ID])

    assert result.exit_code == 1
    assert mock_client.get.call_count == 1
    assert "API error" in result.output


@patch("al.inventory.cli.httpx_client")
def test_subject_get_404_on_attributes_exits_1(mock_client_class) -> None:
    """First call OK; 404 on attributes → exit 1, stderr contains API error."""
    resp_subject = _make_ok_response(SUBJECT_BODY)
    resp_attrs = _make_error_response(404, '{"detail": "Subject not found"}')

    mock_client = MagicMock()
    mock_client.get.side_effect = [resp_subject, resp_attrs]
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["inventory", "subject", SUBJECT_ID])

    assert result.exit_code == 1
    assert "API error" in result.output


@patch("al.inventory.cli.httpx_client")
def test_subject_get_connection_refused_exits_1(mock_client_class) -> None:
    """ConnectError causes exit 1 and mentions Connection refused."""
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.ConnectError("refused")
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["inventory", "subject", SUBJECT_ID])

    assert result.exit_code == 1
    assert "Connection refused" in result.output
