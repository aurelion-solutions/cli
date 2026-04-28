"""Tests for al lake compact command."""

import json
from unittest.mock import MagicMock, patch

import httpx
from typer.testing import CliRunner

from main import app

runner = CliRunner()


def _make_mock_client(return_value):
    mock_response = MagicMock()
    mock_response.json.return_value = return_value
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    return mock_client


@patch("al.lake.api.httpx_client")
def test_compact_default_flags_post_correct_body(mock_client_class) -> None:
    """al lake compact (no flags) posts default values to /api/v0/lake/compaction."""
    mock_client = _make_mock_client({"tables": [], "orphan_cleanup_skipped": True})
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["lake", "compact"])

    assert result.exit_code == 0
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args
    assert "/api/v0/lake/compaction" in str(call_args[0][0])
    assert call_args.kwargs["json"] == {
        "table": "all",
        "retention_days": 7,
        "orphan_older_than_hours": 24,
        "target_file_size_mb": 128,
    }


@patch("al.lake.api.httpx_client")
def test_compact_custom_flags_propagate(mock_client_class) -> None:
    """Custom flags are forwarded verbatim in the POST body."""
    mock_client = _make_mock_client({"tables": [], "orphan_cleanup_skipped": False})
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app,
        [
            "lake",
            "compact",
            "--table",
            "raw.access_artifacts",
            "--retention-days",
            "14",
            "--orphan-older-than-hours",
            "48",
            "--target-file-size-mb",
            "256",
        ],
    )

    assert result.exit_code == 0
    call_args = mock_client.post.call_args
    assert call_args.kwargs["json"] == {
        "table": "raw.access_artifacts",
        "retention_days": 14,
        "orphan_older_than_hours": 48,
        "target_file_size_mb": 256,
    }


@patch("al.lake.api.httpx_client")
def test_compact_prints_response_as_indented_json(mock_client_class) -> None:
    """Output is the mocked response body as indented JSON."""
    body = {
        "tables": [
            {
                "table": "raw.access_artifacts",
                "files_rewritten": 5,
                "snapshots_expired": 2,
            }
        ],
        "orphan_cleanup_skipped": True,
        "orphan_cleanup_skip_reason": "orphan_older_than_hours not elapsed",
    }
    mock_client = _make_mock_client(body)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["lake", "compact"])

    assert result.exit_code == 0
    assert json.loads(result.output) == body


@patch("al.lake.api.httpx_client")
def test_compact_invalid_table_rejected_by_typer(mock_client_class) -> None:
    """Invalid --table value is rejected by Typer with exit code 2; no HTTP call made."""
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["lake", "compact", "--table", "foo"])

    assert result.exit_code == 2
    mock_client.post.assert_not_called()


@patch("al.lake.api.httpx_client")
def test_compact_http_500_exits_1(mock_client_class) -> None:
    """HTTP 500 response causes exit 1 and shows status code and body in output."""
    fake_response = MagicMock(spec=httpx.Response)
    fake_response.status_code = 500
    fake_response.text = "boom"
    err = httpx.HTTPStatusError(
        "500 Internal Server Error",
        request=MagicMock(),
        response=fake_response,
    )

    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = err
    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(app, ["lake", "compact"])

    assert result.exit_code == 1
    assert "500" in result.output
    assert "boom" in result.output
