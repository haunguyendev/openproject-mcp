"""Tests cho oauth_metadata (Phase 3A — thin resource server) — thuần, không cần mcp."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

from oauth_metadata import (  # noqa: E402
    authorization_server_metadata,
    needs_challenge,
    protected_resource_metadata,
    www_authenticate_header,
)

MCP = "https://mcp.promete.ai"
OP = "https://manage.promete.ai"


def test_protected_resource_metadata():
    m = protected_resource_metadata(MCP)
    assert m["resource"] == f"{MCP}/mcp"  # resource = endpoint /mcp (khớp URL connector Claude.ai)
    assert m["authorization_servers"] == [MCP]  # MCP tự host AS metadata


def test_authorization_server_metadata_points_at_openproject():
    m = authorization_server_metadata(MCP, OP)
    assert m["issuer"] == MCP  # RFC 8414: issuer khớp URL fetch metadata
    assert m["authorization_endpoint"] == f"{OP}/oauth/authorize"
    assert m["token_endpoint"] == f"{OP}/oauth/token"
    assert m["code_challenge_methods_supported"] == ["S256"]  # PKCE
    assert "api_v3" in m["scopes_supported"]
    assert "authorization_code" in m["grant_types_supported"]
    assert "code" in m["response_types_supported"]


def test_trailing_slashes_normalized():
    m = authorization_server_metadata(MCP + "/", OP + "/")
    assert m["issuer"] == MCP
    assert m["authorization_endpoint"] == f"{OP}/oauth/authorize"


def test_www_authenticate_header():
    h = www_authenticate_header(MCP)
    assert h == (
        f'Bearer resource_metadata="{MCP}/.well-known/oauth-protected-resource/mcp", scope="api_v3"'
    )


def test_needs_challenge_multi_user_no_bearer():
    # OAuth multi-user (không env key) + không Bearer → thách thức 401
    assert needs_challenge("", "") is True


def test_no_challenge_with_env_key_single_user():
    # http đơn-user (env key set) → fallback env, KHÔNG thách thức (giữ smoke Phase 2/4)
    assert needs_challenge("", "some-api-key") is False


def test_no_challenge_when_bearer_present():
    assert needs_challenge("Bearer abc123", "") is False
    assert needs_challenge("bearer abc123", "some-key") is False


def test_empty_bearer_is_challenged():
    assert needs_challenge("Bearer ", "") is True  # token rỗng = chưa xác thực
