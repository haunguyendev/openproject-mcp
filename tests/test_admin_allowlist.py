"""Tests cho allowlist runtime filter + predicate destructive (Phase 4) — không cần mcp.

Dùng FakeMcp mô phỏng bề mặt FastMCP mà allowlist.install cần (list_tools/call_tool +
_mcp_server.list_tools()/call_tool()), nên chạy được với lệnh test `--with httpx` hiện tại.
"""

import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import allowlist  # noqa: E402
from config import admin_destructive_enabled, is_destructive  # noqa: E402

DESTRUCTIVE = [
    "delete_work_package",
    "delete_news",
    "remove_member",
    "create_project",
    "update_project",
    "bulk_create_work_packages",
    "bulk_update_work_packages",
]
SAFE = ["list_work_packages", "whoami", "get_work_package", "log_time"]


# --- predicate: is_destructive ---


def test_is_destructive_set():
    for name in DESTRUCTIVE:
        assert is_destructive(name), name
    for name in SAFE:
        assert not is_destructive(name), name


# --- predicate: admin_destructive_enabled (transport-aware + override) ---


def test_stdio_default_enabled():
    assert admin_destructive_enabled({}) is True


def test_http_default_disabled():
    assert admin_destructive_enabled({"MCP_TRANSPORT": "http"}) is False


def test_env_override_both_ways():
    # bật trên http
    on_http = {"MCP_TRANSPORT": "http", "OP_MCP_ENABLE_ADMIN_DESTRUCTIVE": "true"}
    assert admin_destructive_enabled(on_http)
    # tắt trên stdio
    assert not admin_destructive_enabled({"OP_MCP_ENABLE_ADMIN_DESTRUCTIVE": "false"})


# --- runtime filter qua allowlist.install (FakeMcp) ---


class _FakeTool:
    def __init__(self, name):
        self.name = name


class _FakeLowlevel:
    def list_tools(self):
        return lambda fn: fn

    def call_tool(self, validate_input=False):
        return lambda fn: fn


class _FakeMcp:
    def __init__(self, names):
        self._all = [_FakeTool(n) for n in names]
        self._mcp_server = _FakeLowlevel()

    async def list_tools(self):
        return list(self._all)

    async def call_tool(self, name, arguments):
        return {"called": name}


@pytest.fixture
def fake_mcp():
    m = _FakeMcp(DESTRUCTIVE + SAFE)
    allowlist.install(m)
    return m


def test_list_tools_full_when_enabled(monkeypatch, fake_mcp):
    monkeypatch.delenv("MCP_TRANSPORT", raising=False)  # stdio default → enabled
    monkeypatch.delenv("OP_MCP_ENABLE_ADMIN_DESTRUCTIVE", raising=False)
    names = {t.name for t in asyncio.run(fake_mcp.list_tools())}
    assert names == set(DESTRUCTIVE + SAFE)


def test_list_tools_filtered_on_http(monkeypatch, fake_mcp):
    monkeypatch.setenv("MCP_TRANSPORT", "http")
    monkeypatch.delenv("OP_MCP_ENABLE_ADMIN_DESTRUCTIVE", raising=False)
    names = {t.name for t in asyncio.run(fake_mcp.list_tools())}
    assert names == set(SAFE)  # 7 destructive bị ẩn
    assert not (names & set(DESTRUCTIVE))


def test_dispatch_blocks_hidden_tool(monkeypatch, fake_mcp):
    monkeypatch.setenv("MCP_TRANSPORT", "http")
    monkeypatch.delenv("OP_MCP_ENABLE_ADMIN_DESTRUCTIVE", raising=False)
    with pytest.raises(ValueError) as e:
        asyncio.run(fake_mcp.call_tool("delete_work_package", {"wp_id": 1}))
    assert "delete_work_package" in str(e.value)
    # safe tool vẫn gọi được
    assert asyncio.run(fake_mcp.call_tool("whoami", {}))["called"] == "whoami"


def test_dispatch_allows_when_env_enabled(monkeypatch, fake_mcp):
    monkeypatch.setenv("MCP_TRANSPORT", "http")
    monkeypatch.setenv("OP_MCP_ENABLE_ADMIN_DESTRUCTIVE", "true")
    assert asyncio.run(fake_mcp.call_tool("delete_work_package", {"wp_id": 1}))["called"] == (
        "delete_work_package"
    )
