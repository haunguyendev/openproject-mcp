"""OAuth metadata + thử thách 401 cho MCP làm Resource Server (Phase 3A — thin).

MCP KHÔNG implement login. Nó chỉ quảng bá OpenProject làm Authorization Server qua
metadata tĩnh (vì OpenProject instance không expose discovery), rồi Claude.ai tự chạy
OAuth (PKCE) thẳng tới OpenProject. Bearer trả về được op_client đọc per-request (Phase 2).

- RFC 9728 `/.well-known/oauth-protected-resource`: chỉ ra AS là chính URL công khai của MCP.
- RFC 8414 `/.well-known/oauth-authorization-server`: issuer = MCP URL, nhưng authorize/token
  endpoint trỏ thẳng OpenProject (được phép — endpoint có thể khác host với issuer).
- 401 + `WWW-Authenticate` kích hoạt luồng OAuth của Claude.ai (chỉ khi multi-user, không env key).
"""

PROTECTED_RESOURCE_PATH = "/.well-known/oauth-protected-resource"
MCP_PATH = "/mcp"  # endpoint Streamable HTTP (Claude.ai kết nối tới {public_url}/mcp)


def mcp_resource(public_url: str) -> str:
    """Định danh resource = chính endpoint MCP ({public_url}/mcp).

    Claude.ai gửi resource này làm param RFC 8707 và yêu cầu khớp URL connector (có path).
    """
    return public_url.rstrip("/") + MCP_PATH


def protected_resource_metadata(public_url: str) -> dict:
    """RFC 9728 — resource = endpoint /mcp; AS = chính MCP (tự host AS metadata)."""
    base = public_url.rstrip("/")
    return {"resource": mcp_resource(base), "authorization_servers": [base]}


def authorization_server_metadata(public_url: str, op_url: str) -> dict:
    """RFC 8414 — issuer = MCP, endpoint authorize/token = OpenProject (Doorkeeper)."""
    issuer = public_url.rstrip("/")
    op = op_url.rstrip("/")
    return {
        "issuer": issuer,
        "authorization_endpoint": f"{op}/oauth/authorize",
        "token_endpoint": f"{op}/oauth/token",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
        "scopes_supported": ["api_v3"],
        "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
    }


def www_authenticate_header(public_url: str) -> str:
    """Header chỉ Claude.ai tới protected-resource metadata (bản path-suffixed) + scope."""
    base = public_url.rstrip("/")
    prm_url = f"{base}{PROTECTED_RESOURCE_PATH}{MCP_PATH}"  # PRM cho resource .../mcp
    return f'Bearer resource_metadata="{prm_url}", scope="api_v3"'


def needs_challenge(authorization_header: str, env_api_key: str) -> bool:
    """Có nên trả 401 thách thức không?

    Chỉ thách thức khi KHÔNG có Bearer **và** KHÔNG có env key (deploy multi-user OAuth thật).
    Có env key = chế độ đơn-user → fallback env, không thách thức (giữ smoke Phase 2/4).
    """
    has_bearer = bool(authorization_header) and authorization_header.lower().startswith("bearer ")
    token = authorization_header[7:].strip() if has_bearer else ""
    return not token and not env_api_key
