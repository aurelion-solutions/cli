"""Pytest configuration."""

import sys
from typing import Any
from unittest.mock import MagicMock
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def make_mock_http_client(
    method: str,
    *,
    return_value: Any | None = None,
    status_code: int = 200,
    raise_for_status_exc: Exception | None = None,
) -> MagicMock:
    """Return a MagicMock wired as an httpx context manager.

    The named HTTP method (get/post/patch/delete) is pre-configured to return
    a response mock with .json(), .status_code, and .raise_for_status.
    The factory does NOT import httpx — callers construct exceptions themselves.
    """
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = return_value if return_value is not None else {}
    if raise_for_status_exc is not None:
        mock_response.raise_for_status = MagicMock(side_effect=raise_for_status_exc)
    else:
        mock_response.raise_for_status = MagicMock()

    mock_client = MagicMock()
    getattr(mock_client, method).return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    return mock_client


@pytest.fixture
def mock_http_client():
    """Yield the make_mock_http_client factory for use in tests.

    Explicit (not autouse). Tests call:
        mock_http_client("get", return_value=[...])
    """
    yield make_mock_http_client
