"""Parametrized simple delete (DELETE) endpoint tests.

Consolidates (Phase 17 Step 22):
  test_app_delete, test_secrets_delete, test_lake_batches_delete.
"""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from main import app

runner = CliRunner()

_UUID = "550e8400-e29b-41d4-a716-446655440000"


@dataclass(frozen=True, slots=True)
class DeleteTestCase:
    test_id: str
    patch_target: str
    argv: list[str]
    expected_url_substring: str
    expected_output_substring: str | None
    expected_params: dict[str, str] | None
    status_code: int = 204


_CASES: list[DeleteTestCase] = [
    DeleteTestCase(
        test_id="app-delete",
        patch_target="al.app.cli.httpx_client",
        argv=["app", "delete", "--app-id", _UUID],
        expected_url_substring=f"/api/v0/applications/{_UUID}",
        expected_output_substring="Application deleted",
        expected_params=None,
    ),
    DeleteTestCase(
        test_id="secrets-delete",
        patch_target="al.secrets.cli.httpx_client",
        argv=[
            "secrets",
            "delete",
            "--key",
            "github/token",
            "--provider",
            "file",
            "--namespace",
            "default",
        ],
        expected_url_substring="/api/v0/secrets/file/",
        expected_output_substring="Secret deleted",
        expected_params={"namespace": "default"},
    ),
    DeleteTestCase(
        test_id="lake-batches-delete",
        patch_target="al.datalake.cli.httpx_client",
        argv=["datalake", "batches", "delete", _UUID],
        expected_url_substring=f"/api/v0/datalake/batches/{_UUID}",
        expected_output_substring="Lake batch deleted",
        expected_params=None,
    ),
]


@pytest.mark.parametrize("case", _CASES, ids=[c.test_id for c in _CASES])
def test_delete_happy_path(case: DeleteTestCase) -> None:
    """Each delete command calls DELETE on the expected URL."""
    from tests.conftest import make_mock_http_client  # noqa: PLC0415

    mock_client = make_mock_http_client(
        "delete",
        status_code=case.status_code,
    )

    with patch(case.patch_target) as mock_client_class:
        mock_client_class.return_value = mock_client
        result = runner.invoke(app, case.argv)

    assert result.exit_code == 0, result.output
    mock_client.delete.assert_called_once()
    call_args = mock_client.delete.call_args
    assert case.expected_url_substring in str(call_args[0][0])

    if case.expected_params is not None:
        actual_params = call_args[1].get("params", {})
        for key, val in case.expected_params.items():
            assert actual_params.get(key) == val, (
                f"Expected params[{key!r}]={val!r}, got {actual_params!r}"
            )

    if case.expected_output_substring is not None:
        assert case.expected_output_substring in result.output, (
            f"Expected {case.expected_output_substring!r} in output: {result.output!r}"
        )
