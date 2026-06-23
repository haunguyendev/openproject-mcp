"""Starlette app cho http mode: MCP endpoint + OAuth resource-server metadata (Phase 3A).

Bọc app Streamable HTTP của FastMCP trong một Starlette ngoài để thêm:
- 2 endpoint metadata tĩnh (RFC 9728 + 8414) quảng bá OpenProject làm Authorization Server.
- Thử thách 401 `WWW-Authenticate` ở mount MCP → kích hoạt OAuth của Claude.ai (chỉ multi-user).

MCP không tự cấp token; Claude.ai chạy OAuth thẳng với OpenProject (PKCE) rồi gửi Bearer,
op_client đọc per-request (Phase 2). Stateless: hết hạn → Claude.ai tự xin lại (401).
"""

import config
import oauth_metadata as om
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from starlette.types import ASGIApp, Receive, Scope, Send


class OAuthChallenge:
    """Wrapper ASGI: trả 401 + WWW-Authenticate khi request MCP thiếu Bearer (và không env key)."""

    def __init__(self, app: ASGIApp, public_url: str) -> None:
        self.app = app
        self.public_url = public_url

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            headers = dict(scope.get("headers") or [])
            auth = headers.get(b"authorization", b"").decode("latin-1")
            if om.needs_challenge(auth, config.API_KEY):
                await self._challenge(send)
                return
        await self.app(scope, receive, send)

    async def _challenge(self, send: Send) -> None:
        body = b'{"error":"unauthorized","error_description":"OAuth required"}'
        await send(
            {
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    (b"www-authenticate", om.www_authenticate_header(self.public_url).encode()),
                    (b"content-type", b"application/json"),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})


def build_http_app(mcp, cfg: config.TransportConfig) -> Starlette:
    """Dựng Starlette: /.well-known/* (public) + mount MCP (có thử thách 401)."""
    public_url = cfg.public_url
    op_url = config.BASE_URL

    async def protected_resource(_request):
        return JSONResponse(om.protected_resource_metadata(public_url))

    async def auth_server(_request):
        meta = om.authorization_server_metadata(
            public_url, op_url, dcr_client=config.oauth_client()
        )
        return JSONResponse(meta)

    async def register(request):
        """DCR (RFC 7591): trả client pre-registered → Claude.ai tự đăng ký, user khỏi dán."""
        client = config.oauth_client()
        if client is None:
            return JSONResponse({"error": "registration_not_supported"}, status_code=404)
        try:
            requested = await request.json()
        except Exception:
            requested = {}
        cid, secret = client
        return JSONResponse(
            om.client_registration_response(cid, secret, requested), status_code=201
        )

    mcp_asgi = mcp.streamable_http_app()  # đã gắn TransportSecuritySettings qua mcp.settings
    return Starlette(
        routes=[
            # PRM phục vụ cả path gốc lẫn path-suffixed /mcp (Claude.ai dò bản /mcp trước).
            Route(om.PROTECTED_RESOURCE_PATH, protected_resource),
            Route(om.PROTECTED_RESOURCE_PATH + om.MCP_PATH, protected_resource),
            Route("/.well-known/oauth-authorization-server", auth_server),
            Route("/oauth/register", register, methods=["POST"]),  # DCR (public)
            Mount("/", app=OAuthChallenge(mcp_asgi, public_url)),
        ],
        lifespan=lambda _app: mcp.session_manager.run(),
    )
