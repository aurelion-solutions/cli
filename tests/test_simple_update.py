"""Parametrized simple update (PATCH) endpoint tests.

Consolidates (Phase 17 Step 22):
  test_inventory_accounts_update, test_inventory_resources_update.

Two test functions:
  1. test_update_happy_path — happy-path PATCH rows
  2. test_update_no_options_error — error-path rows (no flags supplied)
"""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from main import app

runner = CliRunner()


@dataclass(frozen=True, slots=True)
class UpdateHappyCase:
    test_id: str
    patch_target: str
    argv: list[str]
    expected_url_substring: str
    expected_payload_subset: dict[str, object]
    response_data: dict | list
    expected_output_substring: str | None


@dataclass(frozen=True, slots=True)
class UpdateErrorCase:
    test_id: str
    argv: list[str]
    expected_exit_code: int


_HAPPY_CASES: list[UpdateHappyCase] = [
    UpdateHappyCase(
        test_id="accounts-update",
        patch_target="al.inventory.cli.httpx_client",
        argv=[
            "inventory",
            "accounts",
            "update",
            "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "--status",
            "suspended",
        ],
        expected_url_substring="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        expected_payload_subset={"status": "suspended"},
        response_data={
            "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "status": "suspended",
        },
        expected_output_substring=None,
    ),
    UpdateHappyCase(
        test_id="resources-update",
        patch_target="al.inventory.cli.httpx_client",
        argv=[
            "inventory",
            "resources",
            "update",
            "44444444-4444-4444-4444-444444444444",
            "--privilege-level",
            "admin",
        ],
        expected_url_substring="44444444-4444-4444-4444-444444444444",
        expected_payload_subset={"privilege_level": "admin"},
        response_data={
            "id": "44444444-4444-4444-4444-444444444444",
            "privilege_level": "admin",
        },
        expected_output_substring=None,
    ),
]

_ERROR_CASES: list[UpdateErrorCase] = [
    UpdateErrorCase(
        test_id="accounts-update-no-options",
        argv=[
            "inventory",
            "accounts",
            "update",
            "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        ],
        expected_exit_code=1,
    ),
    UpdateErrorCase(
        test_id="resources-update-no-options",
        argv=[
            "inventory",
            "resources",
            "update",
            "55555555-5555-5555-5555-555555555555",
        ],
        expected_exit_code=1,
    ),
]


@pytest.mark.parametrize("case", _HAPPY_CASES, ids=[c.test_id for c in _HAPPY_CASES])
def test_update_happy_path(case: UpdateHappyCase) -> None:
    """Each update command PATCHes the expected URL with the correct payload."""
    from tests.conftest import make_mock_http_client  # noqa: PLC0415

    mock_client = make_mock_http_client(
        "patch",
        return_value=case.response_data,
    )

    with patch(case.patch_target) as mock_client_class:
        mock_client_class.return_value = mock_client
        result = runner.invoke(app, case.argv)

    assert result.exit_code == 0, result.output
    mock_client.patch.assert_called_once()
    call_args = mock_client.patch.call_args
    assert case.expected_url_substring in str(call_args[0][0])

    actual_payload = call_args[1].get("json", {})
    for key, val in case.expected_payload_subset.items():
        assert actual_payload.get(key) == val, (
            f"Expected payload[{key!r}]={val!r}, got {actual_payload!r}"
        )

    if case.expected_output_substring is not None:
        assert case.expected_output_substring in result.output, (
            f"Expected {case.expected_output_substring!r} in output: {result.output!r}"
        )


@pytest.mark.parametrize("case", _ERROR_CASES, ids=[c.test_id for c in _ERROR_CASES])
def test_update_no_options_error(case: UpdateErrorCase) -> None:
    """Update with no option flags exits with non-zero code."""
    result = runner.invoke(app, case.argv)
    assert result.exit_code == case.expected_exit_code, (
        f"Expected exit_code={case.expected_exit_code}, got {result.exit_code}. "
        f"Output: {result.output!r}"
    )
