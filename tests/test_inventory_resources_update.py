"""Tests for al inventory resources update command."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from main import app

runner = CliRunner()


@patch("al.inventory.cli.httpx_client")
def test_resources_update_invokes_patch_endpoint(mock_client_class) -> None:
    """al inventory resources update <id> --privilege-level admin invokes PATCH."""
    resource_id = "44444444-4444-4444-4444-444444444444"
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": resource_id, "privilege_level": "admin"}
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.patch.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app,
        ["inventory", "resources", "update", resource_id, "--privilege-level", "admin"],
    )

    assert result.exit_code == 0
    mock_client.patch.assert_called_once()
    call_args = mock_client.patch.call_args
    assert resource_id in str(call_args[0][0])
    payload = call_args[1].get("json", {})
    assert payload["privilege_level"] == "admin"


def test_resources_update_no_options_exits_with_error() -> None:
    """al inventory resources update <id> with no options exits with code 1."""
    resource_id = "55555555-5555-5555-5555-555555555555"
    result = runner.invoke(app, ["inventory", "resources", "update", resource_id])
    assert result.exit_code == 1
