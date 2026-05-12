"""Parametrized read-only endpoint tests.

Consolidates 21 trivial test files (Phase 17 Step 22):
  test_employees_list, test_employees_get, test_employees_attributes,
  test_persons_list, test_persons_get, test_persons_attributes,
  test_employee_records_list, test_employee_records_get, test_employee_records_attributes,
  test_nhi_list, test_nhi_get,
  test_connectors_list, test_connectors_get,
  test_app_list,
  test_inventory_accounts_list (2 rows), test_inventory_accounts_get,
  test_inventory_resources_list (2 rows), test_inventory_resources_get,
  test_lake_batches_get, test_lake_batches_data,
  test_secrets_list (2 rows).

Each row id matches the original filename token so `pytest -v` stays traceable.
"""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from main import app

runner = CliRunner()

_UUID = "550e8400-e29b-41d4-a716-446655440000"
_UUID2 = "660e8400-e29b-41d4-a716-446655440001"


@dataclass(frozen=True, slots=True)
class ReadOnlyTestCase:
    test_id: str
    patch_target: str
    argv: list[str]
    expected_url_substring: str
    response_data: dict | list
    expected_output_substring: str | None
    expected_query_params: dict[str, str] | None


_CASES: list[ReadOnlyTestCase] = [
    # --- employees ---
    ReadOnlyTestCase(
        test_id="employees-list",
        patch_target="al.employees.cli.httpx_client",
        argv=["employees", "list"],
        expected_url_substring="/api/v0/employees",
        response_data={
            "items": [
                {
                    "id": _UUID,
                    "person_id": _UUID2,
                    "is_locked": False,
                    "description": "Alice",
                    "org_unit_id": None,
                }
            ],
            "total": 1,
            "limit": 1000,
            "offset": 0,
        },
        expected_output_substring=None,
        expected_query_params={"limit": 1000, "offset": 0},
    ),
    ReadOnlyTestCase(
        test_id="employees-list-custom-pagination",
        patch_target="al.employees.cli.httpx_client",
        argv=["employees", "list", "--limit", "25", "--offset", "50"],
        expected_url_substring="/api/v0/employees",
        response_data={
            "items": [],
            "total": 100,
            "limit": 25,
            "offset": 50,
        },
        expected_output_substring=None,
        expected_query_params={"limit": 25, "offset": 50},
    ),
    ReadOnlyTestCase(
        test_id="employees-get",
        patch_target="al.employees.cli.httpx_client",
        argv=["employees", "get", _UUID],
        expected_url_substring=f"/api/v0/employees/{_UUID}",
        response_data={
            "id": _UUID,
            "person_id": _UUID2,
            "is_locked": False,
            "description": "Alice",
        },
        expected_output_substring=None,
        expected_query_params=None,
    ),
    ReadOnlyTestCase(
        test_id="employees-attributes",
        patch_target="al.employees.cli.httpx_client",
        argv=["employees", "attributes", _UUID],
        expected_url_substring=f"/api/v0/employees/{_UUID}/attributes",
        response_data=[
            {
                "id": "770e8400-e29b-41d4-a716-446655440002",
                "employee_id": _UUID,
                "key": "title",
                "value": "Engineer",
            }
        ],
        expected_output_substring=None,
        expected_query_params=None,
    ),
    # --- persons ---
    ReadOnlyTestCase(
        test_id="persons-list",
        patch_target="al.persons.cli.httpx_client",
        argv=["persons", "list"],
        expected_url_substring="/api/v0/persons",
        response_data={
            "items": [{"id": _UUID, "external_id": "ext-1", "full_name": "Alice"}],
            "total": 1,
            "limit": 1000,
            "offset": 0,
        },
        expected_output_substring=None,
        expected_query_params={"limit": 1000, "offset": 0},
    ),
    ReadOnlyTestCase(
        test_id="persons-list-custom-pagination",
        patch_target="al.persons.cli.httpx_client",
        argv=["persons", "list", "--limit", "25", "--offset", "50"],
        expected_url_substring="/api/v0/persons",
        response_data={
            "items": [],
            "total": 200,
            "limit": 25,
            "offset": 50,
        },
        expected_output_substring=None,
        expected_query_params={"limit": 25, "offset": 50},
    ),
    ReadOnlyTestCase(
        test_id="persons-get",
        patch_target="al.persons.cli.httpx_client",
        argv=["persons", "get", _UUID],
        expected_url_substring=f"/api/v0/persons/{_UUID}",
        response_data={"id": _UUID, "external_id": "ext-1", "description": "Alice"},
        expected_output_substring=None,
        expected_query_params=None,
    ),
    ReadOnlyTestCase(
        test_id="persons-attributes",
        patch_target="al.persons.cli.httpx_client",
        argv=["persons", "attributes", _UUID],
        expected_url_substring=f"/api/v0/persons/{_UUID}/attributes",
        response_data=[
            {
                "id": "a1b2c3d4-0000-0000-0000-000000000001",
                "person_id": _UUID,
                "key": "dept",
                "value": "Eng",
            }
        ],
        expected_output_substring=None,
        expected_query_params=None,
    ),
    # --- employee-records ---
    ReadOnlyTestCase(
        test_id="employee-records-list",
        patch_target="al.employee_records.cli.httpx_client",
        argv=["employee-records", "list"],
        expected_url_substring="/api/v0/employee-records",
        response_data=[
            {
                "id": _UUID,
                "external_id": "rec-1",
                "application_id": _UUID2,
                "description": "Alice",
            }
        ],
        expected_output_substring=None,
        expected_query_params=None,
    ),
    ReadOnlyTestCase(
        test_id="employee-records-get",
        patch_target="al.employee_records.cli.httpx_client",
        argv=["employee-records", "get", _UUID],
        expected_url_substring=f"/api/v0/employee-records/{_UUID}",
        response_data={
            "id": _UUID,
            "external_id": "rec-1",
            "application_id": _UUID2,
            "description": "Alice",
        },
        expected_output_substring=None,
        expected_query_params=None,
    ),
    ReadOnlyTestCase(
        test_id="employee-records-attributes",
        patch_target="al.employee_records.cli.httpx_client",
        argv=["employee-records", "attributes", _UUID],
        expected_url_substring=f"/api/v0/employee-records/{_UUID}/attributes",
        response_data=[
            {
                "id": "770e8400-e29b-41d4-a716-446655440002",
                "employee_record_id": _UUID,
                "key": "title",
                "value": "Engineer",
            }
        ],
        expected_output_substring=None,
        expected_query_params=None,
    ),
    # --- nhi ---
    ReadOnlyTestCase(
        test_id="nhi-list",
        patch_target="al.nhi.cli.httpx_client",
        argv=["nhi", "list"],
        expected_url_substring="/api/v0/nhi",
        response_data=[
            {
                "id": _UUID,
                "external_id": "nhi-1",
                "name": "Bot",
                "kind": "bot",
                "description": None,
                "is_locked": False,
                "owner_employee_id": None,
                "application_id": None,
            }
        ],
        expected_output_substring=None,
        expected_query_params=None,
    ),
    ReadOnlyTestCase(
        test_id="nhi-get",
        patch_target="al.nhi.cli.httpx_client",
        argv=["nhi", "get", _UUID],
        expected_url_substring=f"/api/v0/nhi/{_UUID}",
        response_data={
            "id": _UUID,
            "external_id": "nhi-1",
            "name": "Bot",
            "kind": "bot",
            "description": None,
            "is_locked": False,
            "owner_employee_id": None,
            "application_id": None,
        },
        expected_output_substring=None,
        expected_query_params=None,
    ),
    # --- connectors ---
    ReadOnlyTestCase(
        test_id="connectors-list",
        patch_target="al.connectors.cli.httpx_client",
        argv=["app", "connectors", "list"],
        expected_url_substring="/api/v0/connector-instances",
        response_data=[
            {
                "id": _UUID,
                "instance_id": "runtime-a",
                "tags": ["jira"],
                "is_online": True,
                "last_seen_at": "2025-01-01T00:00:00Z",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
            }
        ],
        expected_output_substring="runtime-a",
        expected_query_params=None,
    ),
    ReadOnlyTestCase(
        test_id="connectors-get",
        patch_target="al.connectors.cli.httpx_client",
        argv=["app", "connectors", "get", "runtime-a"],
        expected_url_substring="/connector-instances/runtime-a",
        response_data={
            "id": _UUID,
            "instance_id": "runtime-a",
            "tags": ["jira", "eu-segment"],
            "is_online": True,
            "last_seen_at": "2025-01-01T00:00:00Z",
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z",
        },
        expected_output_substring="runtime-a",
        expected_query_params=None,
    ),
    # --- app list ---
    ReadOnlyTestCase(
        test_id="app-list",
        patch_target="al.app.cli.httpx_client",
        argv=["app", "list"],
        expected_url_substring="/api/v0/applications",
        response_data=[
            {
                "id": _UUID,
                "name": "my-app",
                "config": {},
                "required_connector_tags": [],
                "is_active": True,
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
            }
        ],
        expected_output_substring=_UUID,
        expected_query_params=None,
    ),
    # --- inventory accounts ---
    ReadOnlyTestCase(
        test_id="accounts-list",
        patch_target="al.inventory.cli.httpx_client",
        argv=["inventory", "accounts", "list"],
        expected_url_substring="/api/v0/accounts",
        response_data=[],
        expected_output_substring=None,
        expected_query_params=None,
    ),
    ReadOnlyTestCase(
        test_id="accounts-list-status-filter",
        patch_target="al.inventory.cli.httpx_client",
        argv=["inventory", "accounts", "list", "--status", "active"],
        expected_url_substring="/api/v0/accounts",
        response_data=[],
        expected_output_substring=None,
        expected_query_params={"status": "active"},
    ),
    ReadOnlyTestCase(
        test_id="accounts-get",
        patch_target="al.inventory.cli.httpx_client",
        argv=["inventory", "accounts", "get", _UUID],
        expected_url_substring=f"/api/v0/accounts/{_UUID}",
        response_data={"id": _UUID, "username": "testuser", "status": "active"},
        expected_output_substring=None,
        expected_query_params=None,
    ),
    # --- inventory resources ---
    ReadOnlyTestCase(
        test_id="resources-list",
        patch_target="al.inventory.cli.httpx_client",
        argv=["inventory", "resources", "list"],
        expected_url_substring="/api/v0/resources",
        response_data=[],
        expected_output_substring=None,
        expected_query_params=None,
    ),
    ReadOnlyTestCase(
        test_id="resources-list-kind-filter",
        patch_target="al.inventory.cli.httpx_client",
        argv=["inventory", "resources", "list", "--kind", "database"],
        expected_url_substring="/api/v0/resources",
        response_data=[],
        expected_output_substring=None,
        expected_query_params={"kind": "database"},
    ),
    ReadOnlyTestCase(
        test_id="resources-get",
        patch_target="al.inventory.cli.httpx_client",
        argv=["inventory", "resources", "get", "11111111-1111-1111-1111-111111111111"],
        expected_url_substring="11111111-1111-1111-1111-111111111111",
        response_data={
            "id": "11111111-1111-1111-1111-111111111111",
            "external_id": "ext-001",
            "kind": "table",
        },
        expected_output_substring=None,
        expected_query_params=None,
    ),
    # --- lake batches ---
    ReadOnlyTestCase(
        test_id="lake-batches-get",
        patch_target="al.datalake.cli.httpx_client",
        argv=["datalake", "batches", "get", _UUID],
        expected_url_substring=f"/api/v0/datalake/batches/{_UUID}",
        response_data={
            "id": _UUID,
            "storage_provider": "file",
            "dataset_type": "accounts",
            "row_count": 5,
        },
        expected_output_substring=None,
        expected_query_params=None,
    ),
    ReadOnlyTestCase(
        test_id="lake-batches-data",
        patch_target="al.datalake.cli.httpx_client",
        argv=["datalake", "batches", "data", _UUID],
        expected_url_substring=f"/api/v0/datalake/batches/{_UUID}/data",
        response_data=[{"id": "1"}, {"id": "2"}],
        expected_output_substring="id",
        expected_query_params=None,
    ),
    # --- secrets ---
    ReadOnlyTestCase(
        test_id="secrets-list",
        patch_target="al.secrets.cli.httpx_client",
        argv=["secrets", "list"],
        expected_url_substring="/api/v0/secrets",
        response_data=[
            {"key": "github/token", "provider": "file", "namespace": "default"},
            {"key": "db/password", "provider": "file", "namespace": "prod"},
        ],
        expected_output_substring="github/token",
        expected_query_params=None,
    ),
    ReadOnlyTestCase(
        test_id="secrets-list-empty",
        patch_target="al.secrets.cli.httpx_client",
        argv=["secrets", "list"],
        expected_url_substring="/api/v0/secrets",
        response_data=[],
        expected_output_substring="No secrets",
        expected_query_params=None,
    ),
]


@pytest.mark.parametrize("case", _CASES, ids=[c.test_id for c in _CASES])
def test_url_assertion(case: ReadOnlyTestCase) -> None:
    """Each command hits the expected URL with GET and returns exit_code 0."""
    from tests.conftest import make_mock_http_client  # noqa: PLC0415

    mock_client = make_mock_http_client(
        "get",
        return_value=case.response_data,
    )

    with patch(case.patch_target) as mock_client_class:
        mock_client_class.return_value = mock_client
        result = runner.invoke(app, case.argv)

    assert result.exit_code == 0, result.output
    mock_client.get.assert_called_once()
    call_args = mock_client.get.call_args
    assert case.expected_url_substring in str(call_args[0][0])

    if case.expected_query_params is not None:
        actual_params = call_args[1].get("params", {})
        for key, val in case.expected_query_params.items():
            assert actual_params.get(key) == val, (
                f"Expected params[{key!r}]={val!r}, got {actual_params!r}"
            )

    if case.expected_output_substring is not None:
        assert case.expected_output_substring in result.output, (
            f"Expected {case.expected_output_substring!r} in output: {result.output!r}"
        )
