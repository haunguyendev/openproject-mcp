"""Cấu hình & logging dùng chung cho OpenProject MCP server.

Đọc từ biến môi trường (xem README). stdout dành cho giao thức MCP nên log ra stderr.

Transport: mặc định `stdio` (single-user, env credential — giữ nguyên flow cũ). Đặt
`MCP_TRANSPORT=http` để chạy Streamable HTTP (remote, multi-user, credential per-request).
"""

import logging
import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass, field

BASE_URL = os.environ.get("OPENPROJECT_URL", "").rstrip("/")
API_KEY = os.environ.get("OPENPROJECT_API_KEY", "")
TIMEOUT = float(os.environ.get("OPENPROJECT_TIMEOUT_SECONDS", "30"))

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s openproject-mcp: %(message)s",
)
log = logging.getLogger("openproject-mcp")


@dataclass(frozen=True)
class TransportConfig:
    """Kết quả phân giải transport từ env — thuần, test được, không phụ thuộc mcp."""

    transport: str  # "stdio" | "http"
    host: str = "127.0.0.1"
    port: int = 8000
    stateless_http: bool = True  # per-request identity (verify Phase 1 spike)
    json_response: bool = True  # cấu hình đã verify end-to-end ở spike
    allowed_hosts: list[str] = field(default_factory=list)
    allowed_origins: list[str] = field(default_factory=list)
    public_url: str = ""  # URL công khai HTTPS của MCP (issuer/resource OAuth — Phase 3A)


def _csv(value: str | None) -> list[str]:
    return [p.strip() for p in (value or "").split(",") if p.strip()]


def _int(value: str | None, default: int, name: str) -> int:
    raw = (value or "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as e:
        raise ValueError(f"{name} phải là số nguyên, nhận được {raw!r}.") from e


def _transport_of(env: Mapping[str, str]) -> str:
    return "http" if env.get("MCP_TRANSPORT", "").strip().lower() == "http" else "stdio"


def is_http_transport(env: Mapping[str, str] = os.environ) -> bool:
    """http = remote multi-user (nhiều người có thể cùng ghi) → ảnh hưởng xử lý 409 (M2)."""
    return _transport_of(env) == "http"


def resolve_transport(env: Mapping[str, str]) -> TransportConfig:
    """Phân giải transport + tham số HTTP từ một mapping môi trường.

    `MCP_TRANSPORT` không phải "http" (kể cả rỗng/giá trị lạ) → stdio (an toàn, giữ flow cũ).
    """
    host = env.get("MCP_HOST", "127.0.0.1").strip() or "127.0.0.1"
    port = _int(env.get("MCP_PORT"), 8000, "MCP_PORT")
    public_url = env.get("MCP_PUBLIC_URL", "").strip().rstrip("/") or f"http://{host}:{port}"
    return TransportConfig(
        transport=_transport_of(env),
        host=host,
        port=port,
        stateless_http=env.get("MCP_STATELESS_HTTP", "true").strip().lower() != "false",
        json_response=env.get("MCP_JSON_RESPONSE", "true").strip().lower() != "false",
        allowed_hosts=_csv(env.get("ALLOWED_HOSTS")),
        allowed_origins=_csv(env.get("ALLOWED_ORIGINS")),
        public_url=public_url,
    )


# Tool gây mất dữ liệu/không hồi phục HOẶC tác động lớn (admin/hàng loạt) → ẩn mặc định
# trên remote để đồng nghiệp non-tech không thao tác nhầm. Bộ này grep xác nhận (không đoán):
#   delete_work_package, delete_news, remove_member  → DELETE (mất dữ liệu/thu hồi quyền)
#   create_project, update_project (archive)         → admin dự án (archive làm ẩn dự án)
#   bulk_create_work_packages, bulk_update_work_packages → ghi hàng loạt (sửa/tạo nhiều WP 1 lần)
_DESTRUCTIVE_TOOLS = frozenset(
    {
        "delete_work_package",
        "delete_news",
        "remove_member",
        "create_project",
        "update_project",
        "bulk_create_work_packages",
        "bulk_update_work_packages",
    }
)


def is_destructive(tool_name: str) -> bool:
    """Tool có thuộc nhóm bị hạn chế trên remote không? (1 nguồn sự thật, dùng cả list+dispatch)."""
    return tool_name in _DESTRUCTIVE_TOOLS


def admin_destructive_enabled(env: Mapping[str, str] = os.environ) -> bool:
    """Có cho phép nhóm destructive không? Mặc định transport-aware (stdio full, http restricted).

    `OP_MCP_ENABLE_ADMIN_DESTRUCTIVE` ghi đè 2 chiều (true/1/yes bật; false/0/no tắt) — kể cả
    tắt trên stdio nếu muốn. Đọc env lúc gọi → đếm tool xác định theo cấu hình hiện tại.
    """
    override = env.get("OP_MCP_ENABLE_ADMIN_DESTRUCTIVE", "").strip().lower()
    if override in ("true", "1", "yes"):
        return True
    if override in ("false", "0", "no"):
        return False
    return _transport_of(env) != "http"  # mặc định: stdio bật (giữ 44), http tắt
