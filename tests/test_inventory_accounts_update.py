"""Tests for al inventory accounts update command."""

import uuid
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from main import app

runner = CliRunner()


@patch("al.inventory.cli.httpx_client")
def test_accounts_update_with_status_patches_account(mock_client_class) -> None:
    """al inventory accounts update <id> --status suspended calls PATCH with payload."""
    account_id = str(uuid.uuid4())
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": account_id, "status": "suspended"}
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.patch.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = runner.invoke(
        app, ["inventory", "accounts", "update", account_id, "--status", "suspended"]
    )

    assert result.exit_code == 0
    mock_client.patch.assert_called_once()
    call_kwargs = mock_client.patch.call_args[1]
    assert call_kwargs.get("json") == {"status": "suspended"}


def test_accounts_update_without_options_exits_with_error() -> None:
    """al inventory accounts update <id> with no options exits with code 1."""
    account_id = str(uuid.uuid4())

    result = runner.invoke(app, ["inventory", "accounts", "update", account_id])

    assert result.exit_code == 1
    assert "--status or --subject" in result.output or (
        result.stderr_bytes is not None
        and b"--status or --subject" in result.stderr_bytes
    )
