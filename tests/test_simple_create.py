"""Parametrized simple create (POST) endpoint tests.

Consolidates (Phase 17 Step 22):
  test_nhi_create, test_secrets_create, test_lake_batches_create,
  test_inventory_resources_create.
"""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from main import app

runner = CliRunner()

_UUID = "550e8400-e29b-41d4-a716-446655440000"
_APP_ID = "22222222-2222-2222-2222-222222222222"


@dataclass(frozen=True, slots=True)
class CreateTestCase:
    test_id: str
    patch_target: str
    argv: list[str]
    expected_url_substring: str
    response_data: dict | list
    expected_payload_subset: dict[str, object]
    expected_output_substring: str | None
    status_code: int = 200


_CASES: list[CreateTestCase] = [
    CreateTestCase(
        test_id="nhi-create",
        patch_target="al.nhi.cli.httpx_client",
        argv=[
            "nhi",
            "create",
            "--external-id",
            "new-nhi",
            "--name",
            "Svc",
            "--kind",
            "service_account",
        ],
        expected_url_substring="/api/v0/nhi",
        response_data={
            "id": _UUID,
            "external_id": "new-nhi",
            "name": "Svc",
            "kind": "service_account",
            "description": None,
            "is_locked": False,
            "owner_employee_id": None,
            "application_id": None,
        },
        expected_payload_subset={"external_id": "new-nhi"},
        expected_output_substring=None,
    ),
    CreateTestCase(
        test_id="secrets-create",
        patch_target="al.secrets.cli.httpx_client",
        argv=[
            "secrets",
            "create",
            "--key",
            "github/token",
            "--provider",
            "file",
            "--namespace",
            "default",
            "--value",
            "secret123",
        ],
        expected_url_substring="/api/v0/secrets",
        response_data={},
        expected_payload_subset={
            "key": "github/token",
            "provider": "file",
            "namespace": "default",
            "value": "secret123",
        },
        expected_output_substring="Secret created",
    ),
    CreateTestCase(
        test_id="lake-batches-create",
        patch_target="al.datalake.cli.httpx_client",
        argv=[
            "datalake",
            "batches",
            "create",
            "--storage-provider",
            "file",
            "--dataset-type",
            "accounts",
            "--records",
            '[{"id":"1"}]',
        ],
        expected_url_substring="/api/v0/datalake/batches",
        response_data={
            "id": _UUID,
            "storage_provider": "file",
            "dataset_type": "accounts",
            "storage_key": "accounts/uuid",
            "row_count": 1,
            "created_at": "2025-01-01T00:00:00Z",
        },
        expected_payload_subset={
            "storage_provider": "file",
            "dataset_type": "accounts",
        },
        expected_output_substring="Created lake batch",
    ),
    CreateTestCase(
        test_id="resources-create",
        patch_target="al.inventory.cli.httpx_client",
        argv=[
            "inventory",
            "resources",
            "create",
            "--external-id",
            "res-ext-001",
            "--application",
            _APP_ID,
            "--kind",
            "database",
        ],
        expected_url_substring="/api/v0/resources",
        response_data={
            "id": "33333333-3333-3333-3333-333333333333",
            "external_id": "res-ext-001",
            "application_id": _APP_ID,
            "kind": "database",
        },
        expected_payload_subset={
            "external_id": "res-ext-001",
            "application_id": _APP_ID,
            "kind": "database",
        },
        expected_output_substring=None,
    ),
]


@pytest.mark.parametrize("case", _CASES, ids=[c.test_id for c in _CASES])
def test_create_happy_path(case: CreateTestCase) -> None:
    """Each create command POSTs to the expected URL, sends the correct payload."""
    from tests.conftest import make_mock_http_client  # noqa: PLC0415

    mock_client = make_mock_http_client(
        "post",
        return_value=case.response_data,
        status_code=case.status_code,
    )

    with patch(case.patch_target) as mock_client_class:
        mock_client_class.return_value = mock_client
        result = runner.invoke(app, case.argv)

    assert result.exit_code == 0, result.output
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args
    assert case.expected_url_substring in str(call_args[0][0])

    if case.expected_payload_subset:
        actual_payload = call_args[1].get("json", {})
        for key, val in case.expected_payload_subset.items():
            assert actual_payload.get(key) == val, (
                f"Expected payload[{key!r}]={val!r}, got {actual_payload!r}"
            )

    if case.expected_output_substring is not None:
        assert case.expected_output_substring in result.output, (
            f"Expected {case.expected_output_substring!r} in output: {result.output!r}"
        )
