"""Unit tests cho config.resolve_transport — thuần, không cần mạng/mcp."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

from config import resolve_transport  # noqa: E402


def test_empty_env_defaults_to_stdio():
    cfg = resolve_transport({})
    assert cfg.transport == "stdio"


def test_http_transport_defaults():
    cfg = resolve_transport({"MCP_TRANSPORT": "http"})
    assert cfg.transport == "http"
    assert cfg.host == "127.0.0.1"
    assert cfg.port == 8000
    assert cfg.stateless_http is True
    assert cfg.allowed_hosts == []
    assert cfg.allowed_origins == []


def test_overrides_honored():
    cfg = resolve_transport(
        {
            "MCP_TRANSPORT": "http",
            "MCP_HOST": "0.0.0.0",
            "MCP_PORT": "9001",
            "ALLOWED_ORIGINS": "https://a.example.com, https://b.example.com",
            "ALLOWED_HOSTS": "mcp.example.com",
        }
    )
    assert (cfg.host, cfg.port) == ("0.0.0.0", 9001)
    assert cfg.allowed_origins == ["https://a.example.com", "https://b.example.com"]
    assert cfg.allowed_hosts == ["mcp.example.com"]


def test_transport_case_insensitive():
    assert resolve_transport({"MCP_TRANSPORT": "HTTP"}).transport == "http"
    assert resolve_transport({"MCP_TRANSPORT": "Stdio"}).transport == "stdio"


def test_unknown_transport_falls_back_to_stdio():
    # An toàn: giá trị lạ → stdio (không bật HTTP ngoài ý muốn).
    assert resolve_transport({"MCP_TRANSPORT": "websocket"}).transport == "stdio"


def test_blank_csv_entries_dropped():
    cfg = resolve_transport({"MCP_TRANSPORT": "http", "ALLOWED_ORIGINS": " , https://a.com , "})
    assert cfg.allowed_origins == ["https://a.com"]
