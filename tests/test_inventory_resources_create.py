"""Tests for al inventory resources create command."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from main import app

runner = CliRunner()


@patch("al.inventory.cli.httpx_client")
def test_resources_create_invokes_post_endpoint(mock_client_class) -> None:
    """al inventory resources create invokes POST /api/v0/resources."""
    app_id = "22222222-2222-2222-2222-222222222222"
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "id": "33333333-3333-3333-3333-333333333333",
        "external_id": "res-ext-001",
        "application_id": app_id,
        "kind": "database",
    }
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app,
        [
            "inventory",
            "resources",
            "create",
            "--external-id",
            "res-ext-001",
            "--application",
            app_id,
            "--kind",
            "database",
        ],
    )

    assert result.exit_code == 0
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args
    assert "/api/v0/resources" in str(call_args[0][0])
    payload = call_args[1].get("json", {})
    assert payload["external_id"] == "res-ext-001"
    assert payload["application_id"] == app_id
    assert payload["kind"] == "database"
