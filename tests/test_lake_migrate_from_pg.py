"""Tests for al lake migrate-from-pg command."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import httpx
from typer.testing import CliRunner

from main import app

runner = CliRunner()

_RUN_PENDING = {
    "id": "11111111-1111-1111-1111-111111111111",
    "dataset": "access_artifacts",
    "status": "pending",
    "rows_read": 0,
    "rows_written": 0,
    "last_processed_id": None,
    "batch_size": 5000,
    "lake_batch_id": "22222222-2222-2222-2222-222222222222",
    "created_at": "2026-04-27T12:00:00+00:00",
}

_RUN_COMPLETED = {
    **_RUN_PENDING,
    "status": "completed",
    "rows_read": 100,
    "rows_written": 100,
}


def _make_http_client_mock(post_response, get_responses: list):
    """Return a context-managed mock for LakeMigrationClient."""
    mock_client = MagicMock()

    def start_side_effect(**kwargs):
        return post_response

    mock_client.start_migration.side_effect = start_side_effect

    get_iter = iter(get_responses)

    def get_side_effect(run_id):
        return next(get_iter)

    mock_client.get_run.side_effect = get_side_effect
    return mock_client


@patch("al.lake.cli.LakeMigrationClient")
@patch("al.lake.cli.time.sleep", return_value=None)
def test_migrate_from_pg_happy_path(mock_sleep, MockClient):
    """al lake migrate-from-pg --dataset access_artifacts exits 0 on completed."""
    instance = _make_http_client_mock(
        post_response=_RUN_PENDING,
        get_responses=[_RUN_COMPLETED],
    )
    MockClient.return_value = instance

    result = runner.invoke(
        app,
        [
            "lake",
            "migrate-from-pg",
            "--dataset",
            "access_artifacts",
            "--poll-interval",
            "0",
        ],
    )

    assert result.exit_code == 0, result.output
    # Extract JSON from output (progress lines precede it on same stream in Typer's CliRunner)
    output = result.output
    json_start = output.find("{")
    assert json_start >= 0, f"No JSON found in output: {output!r}"
    stdout_json = json.loads(output[json_start:])
    run_id = _RUN_PENDING["id"]
    assert run_id in stdout_json
    assert stdout_json[run_id]["status"] == "completed"
    assert stdout_json[run_id]["rows_read"] == 100


@patch("al.lake.cli.LakeMigrationClient")
@patch("al.lake.cli.time.sleep", return_value=None)
def test_migrate_from_pg_failed_exits_1(mock_sleep, MockClient):
    """al lake migrate-from-pg exits 1 when run status=failed."""
    failed_run = {**_RUN_PENDING, "status": "failed", "error": "test error"}
    instance = _make_http_client_mock(
        post_response=_RUN_PENDING,
        get_responses=[failed_run],
    )
    MockClient.return_value = instance

    result = runner.invoke(
        app,
        [
            "lake",
            "migrate-from-pg",
            "--dataset",
            "access_artifacts",
            "--poll-interval",
            "0",
        ],
    )
    assert result.exit_code == 1


@patch("al.lake.cli.LakeMigrationClient")
@patch("al.lake.cli.time.sleep", return_value=None)
def test_migrate_from_pg_resume_404_exits_1(mock_sleep, MockClient):
    """--resume <nonexistent-id> with mocked 404 exits 1."""
    instance = MagicMock()
    instance.start_migration.side_effect = httpx.HTTPStatusError(
        "404",
        request=MagicMock(),
        response=MagicMock(status_code=404, text="not found"),
    )
    MockClient.return_value = instance

    result = runner.invoke(
        app,
        [
            "lake",
            "migrate-from-pg",
            "--dataset",
            "access_artifacts",
            "--resume",
            "00000000-0000-0000-0000-000000000001",
            "--poll-interval",
            "0",
        ],
    )
    assert result.exit_code == 1


@patch("al.lake.cli.LakeMigrationClient")
@patch("al.lake.cli.time.sleep", return_value=None)
def test_migrate_from_pg_all_polls_both_runs(mock_sleep, MockClient):
    """--dataset all polls both returned run ids, exits 0 when both complete."""
    run1 = {
        **_RUN_PENDING,
        "id": "aaaaaaaa-0000-0000-0000-000000000001",
        "dataset": "access_artifacts",
    }
    run2 = {
        **_RUN_PENDING,
        "id": "bbbbbbbb-0000-0000-0000-000000000002",
        "dataset": "access_facts",
    }
    run1_done = {**run1, "status": "completed", "rows_read": 50, "rows_written": 50}
    run2_done = {**run2, "status": "completed", "rows_read": 30, "rows_written": 30}

    instance = MagicMock()
    instance.start_migration.return_value = [run1, run2]

    call_count = {"n": 0}

    def get_run(run_id):
        call_count["n"] += 1
        if run_id == run1["id"]:
            return run1_done
        return run2_done

    instance.get_run.side_effect = get_run
    MockClient.return_value = instance

    result = runner.invoke(
        app,
        ["lake", "migrate-from-pg", "--dataset", "all", "--poll-interval", "0"],
    )

    assert result.exit_code == 0, result.output
    json_start = result.output.find("{")
    stdout_json = json.loads(result.output[json_start:])
    assert run1["id"] in stdout_json
    assert run2["id"] in stdout_json
