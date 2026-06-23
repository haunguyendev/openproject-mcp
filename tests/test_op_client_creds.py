"""Unit tests cho op_client.current_creds — per-request credential, không cần mạng/mcp.

Cơ chế lấy request (SDK request_ctx) đã verify ở Phase 1 spike; ở đây monkeypatch
`_current_request` để test thuần logic phân giải credential + fallback + 401 sạch.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import config  # noqa: E402
import op_client  # noqa: E402
from op_client import AuthError, Creds, current_creds  # noqa: E402


class _CIHeaders:
    """Headers giả không phân biệt hoa thường (giống Starlette Headers.get)."""

    def __init__(self, data: dict):
        self._d = {k.lower(): v for k, v in data.items()}

    def get(self, key, default=None):
        return self._d.get(key.lower(), default)


class _FakeReq:
    def __init__(self, headers: dict):
        self.headers = _CIHeaders(headers)


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    """base_url toàn cục cố định; mỗi test tự set request + API_KEY."""
    monkeypatch.setattr(config, "BASE_URL", "https://op.example.com")
    monkeypatch.setattr(op_client, "_current_request", lambda: None)
    op_client._creds_override.set(None)
    yield


def test_env_fallback_when_stdio(monkeypatch):
    # Không có request (stdio) + API_KEY set → Basic apikey:token (hành vi cũ).
    monkeypatch.setattr(config, "API_KEY", "tok-stdio")
    creds = current_creds()
    assert creds == Creds(base_url="https://op.example.com", auth=("apikey", "tok-stdio"))


def test_override_wins(monkeypatch):
    # Seam cho Phase 3 (vault B) + test: override luôn thắng.
    monkeypatch.setattr(config, "API_KEY", "tok-stdio")
    forced = Creds(base_url="https://op.example.com", bearer="forced-bearer")
    token = op_client._creds_override.set(forced)
    try:
        assert current_creds() is forced
    finally:
        op_client._creds_override.reset(token)


def test_bearer_from_request(monkeypatch):
    monkeypatch.setattr(config, "API_KEY", "tok-stdio")  # env tồn tại nhưng Bearer thắng
    monkeypatch.setattr(
        op_client, "_current_request", lambda: _FakeReq({"Authorization": "Bearer abc-123"})
    )
    creds = current_creds()
    assert creds.bearer == "abc-123"
    assert creds.auth is None


def test_http_no_context_raises_clean_401(monkeypatch):
    # http multi-user: không Bearer, không env key → AuthError (401 sạch), KHÔNG lỗi config cũ.
    monkeypatch.setattr(config, "API_KEY", "")
    with pytest.raises(AuthError) as e:
        current_creds()
    assert "401" in str(e.value)
    assert "chưa được cấu hình" not in str(e.value)  # không phải thông điệp config cũ


def test_no_leak_between_two_injects(monkeypatch):
    monkeypatch.setattr(config, "API_KEY", "")
    a = Creds(base_url="https://op.example.com", bearer="user-a")
    t = op_client._creds_override.set(a)
    assert current_creds().bearer == "user-a"
    op_client._creds_override.reset(t)
    b = Creds(base_url="https://op.example.com", bearer="user-b")
    t = op_client._creds_override.set(b)
    assert current_creds().bearer == "user-b"
    op_client._creds_override.reset(t)


def test_request_kwargs_basic_vs_bearer():
    basic = Creds(base_url="x", auth=("apikey", "tok"))
    bearer = Creds(base_url="x", bearer="btok")
    assert op_client._request_kwargs(basic) == {"auth": ("apikey", "tok")}
    assert op_client._request_kwargs(bearer) == {"headers": {"Authorization": "Bearer btok"}}
