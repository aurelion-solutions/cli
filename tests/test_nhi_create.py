"""Tests for al nhi create command."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from main import app

runner = CliRunner()


@patch("al.nhi.cli.httpx_client")
def test_nhi_create_invokes_post_endpoint(mock_client_class) -> None:
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "external_id": "new-nhi",
        "name": "Svc",
        "kind": "service_account",
        "description": None,
        "is_locked": False,
        "owner_employee_id": None,
        "application_id": None,
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
            "nhi",
            "create",
            "--external-id",
            "new-nhi",
            "--name",
            "Svc",
            "--kind",
            "service_account",
        ],
    )

    assert result.exit_code == 0
    mock_client.post.assert_called_once()
    call_kw = mock_client.post.call_args
    assert "/api/v0/nhi" in str(call_kw[0][0])
    assert call_kw[1]["json"]["external_id"] == "new-nhi"
