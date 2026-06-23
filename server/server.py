# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "mcp>=1.2.0",
#     "httpx>=0.27",
# ]
# ///
"""OpenProject MCP server — entry point.

Cấu hình qua biến môi trường (xem README):

  OPENPROJECT_URL              URL của OpenProject (vd: https://your-openproject.example.com)
  OPENPROJECT_API_KEY          API key cá nhân (My account → Access tokens → API)
  OPENPROJECT_TIMEOUT_SECONDS  Timeout request (mặc định 30)

  MCP_TRANSPORT                "stdio" (mặc định) | "http" (Streamable HTTP, remote multi-user)
  MCP_HOST / MCP_PORT          Bind cho http mode (mặc định 127.0.0.1:8000)
  ALLOWED_HOSTS / ALLOWED_ORIGINS  CSV — bắt buộc cho http production sau reverse proxy

stdio: single-user, credential = env (flow cũ, không đổi). http: credential per-request
(xem op_client.current_creds). OpenProject API v3 xác thực Basic Auth: "apikey":API key.

Code được tách module: config (env+transport), op_client (HTTP per-request creds),
formatters (rút gọn JSON), app (FastMCP instance), và các tools_*.py đăng ký tool lên app.mcp.
"""

import os

# Import các module tools để side-effect đăng ký @mcp.tool() lên app.mcp.
import tools_admin  # noqa: F401
import tools_bulk  # noqa: F401
import tools_coder  # noqa: F401
import tools_news  # noqa: F401
import tools_notifications  # noqa: F401
import tools_projects  # noqa: F401
import tools_reports  # noqa: F401
import tools_time  # noqa: F401
import tools_work_packages  # noqa: F401
from app import mcp
from config import API_KEY, BASE_URL, TransportConfig, log, resolve_transport

__version__ = "0.7.0"


def _run_http(cfg: TransportConfig) -> None:
    """Chạy Streamable HTTP (multi-user) + OAuth resource-server metadata (Phase 3A)."""
    import http_app
    import uvicorn
    from mcp.server.transport_security import TransportSecuritySettings

    # FastMCP factory cho host non-loopback mặc định KHÔNG bật bảo vệ → ta bật tường minh.
    allowed_hosts = cfg.allowed_hosts or [f"127.0.0.1:{cfg.port}", f"localhost:{cfg.port}"]
    if not cfg.allowed_hosts:
        log.warning(
            "ALLOWED_HOSTS chưa đặt — mặc định chỉ cho localhost. "
            "Production sau reverse proxy PHẢI đặt ALLOWED_HOSTS=<domain công khai>."
        )
    if API_KEY:
        # http + env key toàn cục = fallback đơn-user: request không Bearer chạy dưới env
        # identity (không 401). OK cho smoke đơn-user; multi-user thật phải BỎ env key.
        log.warning(
            "OPENPROJECT_API_KEY đang set ở http mode → fallback ĐƠN-USER (env identity) "
            "cho request không có Bearer. Multi-user thật: BỎ env key để buộc auth per-user."
        )
    if not cfg.public_url.startswith("https://"):
        # OAuth/Claude.ai yêu cầu HTTPS; metadata sẽ quảng bá issuer/resource không-https → hỏng.
        log.warning(
            "MCP_PUBLIC_URL=%s không phải https — OAuth/Claude.ai cần HTTPS. "
            "Đặt MCP_PUBLIC_URL=https://<domain công khai> khi deploy.",
            cfg.public_url,
        )

    mcp.settings.host = cfg.host
    mcp.settings.port = cfg.port
    mcp.settings.stateless_http = cfg.stateless_http
    mcp.settings.json_response = cfg.json_response
    mcp.settings.transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=allowed_hosts,
        allowed_origins=cfg.allowed_origins,
    )
    log.info(
        "transport=http host=%s port=%s public_url=%s stateless=%s allowed_hosts=%s",
        cfg.host,
        cfg.port,
        cfg.public_url,
        cfg.stateless_http,
        allowed_hosts,
    )
    app = http_app.build_http_app(mcp, cfg)
    uvicorn.run(app, host=cfg.host, port=cfg.port, log_level="warning")


def main() -> None:
    cfg = resolve_transport(os.environ)
    log.info(
        "openproject-mcp v%s — transport=%s base_url=%s api_key_set=%s",
        __version__,
        cfg.transport,
        BASE_URL or "(chưa cấu hình)",
        bool(API_KEY),
    )
    if cfg.transport == "http":
        _run_http(cfg)
    else:
        mcp.run()  # stdio — flow single-user cũ, không đổi


if __name__ == "__main__":
    main()
