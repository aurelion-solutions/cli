"""Tests for al sod resolve-capabilities command."""

import json
from unittest.mock import MagicMock, patch

import httpx
from typer.testing import CliRunner

from main import app

runner = CliRunner()

SOURCE_ENTRY = {
    "application_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    "resource_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
    "action_slug": "read",
    "resource_kind": "document",
    "resource_external_id": "doc-42",
}
RESOLVE_RESPONSE = ["approve_payment", "create_vendor"]


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
def test_resolve_from_file_with_sources_object(mock_client_class, tmp_path) -> None:
    payload = {"sources": [SOURCE_ENTRY]}
    sources_file = tmp_path / "sources.json"
    sources_file.write_text(json.dumps(payload))

    mock_client = _make_mock_client(200, RESOLVE_RESPONSE)
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app, ["sod", "resolve-capabilities", "--file", str(sources_file)]
    )

    assert result.exit_code == 0
    call_body = mock_client.post.call_args[1]["json"]
    assert call_body == payload
    assert "approve_payment" in result.output


@patch("al.sod.cli.httpx_client")
def test_resolve_from_file_with_top_level_list(mock_client_class, tmp_path) -> None:
    sources_file = tmp_path / "sources.json"
    sources_file.write_text(json.dumps([SOURCE_ENTRY]))

    mock_client = _make_mock_client(200, RESOLVE_RESPONSE)
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app, ["sod", "resolve-capabilities", "--file", str(sources_file)]
    )

    assert result.exit_code == 0
    call_body = mock_client.post.call_args[1]["json"]
    assert call_body == {"sources": [SOURCE_ENTRY]}


@patch("al.sod.cli.httpx_client")
def test_resolve_from_stdin(mock_client_class) -> None:
    mock_client = _make_mock_client(200, RESOLVE_RESPONSE)
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app,
        ["sod", "resolve-capabilities"],
        input=json.dumps({"sources": [SOURCE_ENTRY]}),
    )

    assert result.exit_code == 0
    call_url = mock_client.post.call_args[0][0]
    assert "/api/v0/sod/resolve-capabilities" in call_url


@patch("al.sod.cli.httpx_client")
def test_resolve_empty_input(mock_client_class) -> None:
    result = runner.invoke(app, ["sod", "resolve-capabilities"], input="")

    assert result.exit_code == 2
    assert "No input" in result.output
    mock_client_class.assert_not_called()


@patch("al.sod.cli.httpx_client")
def test_resolve_invalid_json(mock_client_class) -> None:
    result = runner.invoke(
        app, ["sod", "resolve-capabilities"], input="{not valid json"
    )

    assert result.exit_code == 2
    assert "Invalid JSON" in result.output
    mock_client_class.assert_not_called()


@patch("al.sod.cli.httpx_client")
def test_resolve_wrong_top_level_shape(mock_client_class) -> None:
    # Object without "sources" key
    result = runner.invoke(
        app,
        ["sod", "resolve-capabilities"],
        input=json.dumps({"wrong_key": [SOURCE_ENTRY]}),
    )

    assert result.exit_code == 2
    assert (
        "expected an object" in result.output.lower()
        or "Invalid input" in result.output
    )
    mock_client_class.assert_not_called()


@patch("al.sod.cli.httpx_client")
def test_resolve_api_error(mock_client_class) -> None:
    mock_client = _make_mock_client(500, {"detail": "Internal Server Error"})
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app,
        ["sod", "resolve-capabilities"],
        input=json.dumps({"sources": [SOURCE_ENTRY]}),
    )

    assert result.exit_code == 1
    assert "API error:" in result.output
