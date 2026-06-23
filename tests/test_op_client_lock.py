"""Unit tests cho op_client.patch_wp_with_lock — monkeypatch _req, không cần mạng."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import op_client  # noqa: E402
from op_client import ConflictError, patch_wp_with_lock  # noqa: E402


def test_explicit_lock_version_skips_get(monkeypatch):
    calls = []

    def fake_req(method, path, *, params=None, body=None):
        calls.append((method, path, body))
        return {"sent": body}

    monkeypatch.setattr(op_client, "_req", fake_req)
    patch_wp_with_lock(10, {"subject": "x"}, lock_version=3)

    assert [c[0] for c in calls] == ["PATCH"]  # không GET khi đã có lock_version
    assert calls[0][2]["lockVersion"] == 3


def test_auto_fetch_lock_version_when_omitted(monkeypatch):
    calls = []

    def fake_req(method, path, *, params=None, body=None):
        calls.append((method, path, body))
        if method == "GET":
            return {"lockVersion": 7}
        return {"sent": body}

    monkeypatch.setattr(op_client, "_req", fake_req)
    out = patch_wp_with_lock(10, {"subject": "x"})

    assert [c[0] for c in calls] == ["GET", "PATCH"]
    assert calls[1][2]["lockVersion"] == 7
    assert out["sent"]["subject"] == "x"


def test_retries_once_on_conflict(monkeypatch):
    monkeypatch.delenv("MCP_TRANSPORT", raising=False)  # stdio: rollup → retry 1 lần
    calls = []
    state = {"patch": 0}

    def fake_req(method, path, *, params=None, body=None):
        calls.append((method, path, body))
        if method == "GET":
            return {"lockVersion": 100 + state["patch"]}
        state["patch"] += 1
        if state["patch"] == 1:
            raise ConflictError("HTTP 409")
        return {"sent": body}

    monkeypatch.setattr(op_client, "_req", fake_req)
    out = patch_wp_with_lock(10, {"subject": "x"})

    assert [c[0] for c in calls] == ["GET", "PATCH", "GET", "PATCH"]  # refetch + retry once
    assert out["sent"]["lockVersion"] == 101  # dùng lockVersion mới sau refetch


def test_double_conflict_propagates(monkeypatch):
    monkeypatch.delenv("MCP_TRANSPORT", raising=False)  # stdio

    def fake_req(method, path, *, params=None, body=None):
        if method == "GET":
            return {"lockVersion": 1}
        raise ConflictError("HTTP 409")

    monkeypatch.setattr(op_client, "_req", fake_req)
    with pytest.raises(ConflictError) as e:
        patch_wp_with_lock(10, {"subject": "x"})
    assert "thử lại" in str(e.value)  # thông điệp rõ ràng sau retry


def test_http_surfaces_conflict_without_overwrite(monkeypatch):
    # M2: http multi-user → 409 lần đầu surface ngay, KHÔNG retry-ghi-đè mù.
    monkeypatch.setenv("MCP_TRANSPORT", "http")
    calls = []

    def fake_req(method, path, *, params=None, body=None):
        calls.append(method)
        if method == "GET":
            return {"lockVersion": 5}
        raise ConflictError("HTTP 409")

    monkeypatch.setattr(op_client, "_req", fake_req)
    with pytest.raises(ConflictError) as e:
        patch_wp_with_lock(10, {"subject": "x"})
    assert calls == ["GET", "PATCH"]  # KHÔNG có GET/PATCH lần hai (không ghi đè)
    assert "người khác" in str(e.value)
