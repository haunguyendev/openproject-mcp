"""HTTP client + request helpers cho OpenProject API v3.

Credential lấy **per-request** (multi-user remote) qua cơ chế đã verify ở Phase 1 spike:
SDK đặt ContextVar `request_ctx` trước khi dispatch tool → op_client đọc request hiện tại
ở đây, KHÔNG cần truyền `ctx` qua 44 tool. Không có request (stdio) → fallback env
(`OPENPROJECT_API_KEY`) → flow single-user cũ giữ nguyên 100% (RÀNG BUỘC SỐ 1).

Auth: HTTP Basic (username "apikey", password = API token) hoặc Bearer (OAuth — Phase 3A).
`OPENPROJECT_URL` là toàn cục (cả nhóm 1 instance) nên client dùng chung 1 base_url.
"""

import json
import time
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any

import config
import httpx
from config import log

# request_ctx của SDK chỉ có khi chạy dưới mcp; pure-helper test (không cài mcp) → None.
try:
    from mcp.server.lowlevel.server import request_ctx
except Exception:  # pragma: no cover - chỉ khi mcp vắng mặt (test thuần)
    request_ctx = None

_RETRYABLE = {429, 502, 503, 504}
_http: httpx.Client | None = None


class ConflictError(RuntimeError):
    """HTTP 409 (optimistic locking) — lockVersion đã cũ vì WP bị sửa đồng thời.

    Tách riêng để caller (patch_wp_with_lock) bắt chính xác và thử lại, thay vì
    nhận RuntimeError chung chung.
    """


class AuthError(RuntimeError):
    """Không có credential per-request khả dụng → ánh xạ thành 401 sạch cho người gọi.

    Phân biệt với lỗi cấu hình cũ ("OPENPROJECT_API_KEY chưa cấu hình"): ở chế độ http
    multi-user, thiếu Bearer/định danh nghĩa là request chưa xác thực, không phải server
    cấu hình sai.
    """


@dataclass(frozen=True)
class Creds:
    """Credential cho MỘT request. base_url toàn cục; chỉ auth/bearer đổi theo user."""

    base_url: str
    auth: tuple[str, str] | None = None  # Basic ("apikey", token)
    bearer: str | None = None  # OAuth bearer (Phase 3A)


# Seam ghi đè credential per-request (test + Phase 3B vault set token theo /c/<id>/).
_creds_override: ContextVar[Creds | None] = ContextVar("op_creds_override", default=None)


def _current_request() -> Any | None:
    """Request HTTP hiện tại từ ContextVar của SDK (None khi stdio hoặc ngoài request)."""
    if request_ctx is None:
        return None
    rc = request_ctx.get(None)
    return getattr(rc, "request", None) if rc is not None else None


def _bearer_from_request(req: Any | None) -> str | None:
    if req is None:
        return None
    header = req.headers.get("authorization")
    if header and header.lower().startswith("bearer "):
        return header.split(None, 1)[1].strip()
    return None


def current_creds() -> Creds:
    """Phân giải credential cho request hiện tại.

    Thứ tự: override (vault/test) → Bearer trong request (OAuth) → env (stdio/http đơn-user)
    → AuthError 401 sạch (http multi-user không định danh).
    """
    override = _creds_override.get(None)
    if override is not None:
        return override

    base = config.BASE_URL
    if not base:
        raise ValueError("OPENPROJECT_URL chưa được cấu hình trong môi trường.")

    bearer = _bearer_from_request(_current_request())
    if bearer:
        return Creds(base_url=base, bearer=bearer)

    if config.API_KEY:  # fallback env: stdio cũ + http single-user smoke
        return Creds(base_url=base, auth=("apikey", config.API_KEY))

    raise AuthError(
        "HTTP 401: request chưa xác thực. Endpoint yêu cầu định danh per-user "
        "(Authorization: Bearer …) hoặc cấu hình OPENPROJECT_API_KEY cho chế độ đơn-user."
    )


def _request_kwargs(creds: Creds) -> dict:
    """kwargs httpx cho từng request: Bearer → header; ngược lại → Basic auth."""
    if creds.bearer:
        return {"headers": {"Authorization": f"Bearer {creds.bearer}"}}
    return {"auth": creds.auth}


def _client(base_url: str) -> httpx.Client:
    """Client dùng chung (pool kết nối), KHÔNG gắn auth — auth truyền per-request (M1).

    1 instance OpenProject → 1 base_url → 1 client; tránh rò rỉ fd/memory của cache cũ.
    """
    global _http
    if _http is None or _http.is_closed:
        _http = httpx.Client(
            base_url=base_url + "/api/v3",
            timeout=config.TIMEOUT,
            follow_redirects=True,
            headers={"Accept": "application/hal+json"},
        )
    return _http


def _error_message(r: httpx.Response) -> str:
    try:
        return r.json().get("message", r.text[:500])
    except ValueError:
        return r.text[:500]


def _req(method: str, path: str, *, params: dict | None = None, body: dict | None = None) -> dict:
    """Gọi API với 1 lần retry cho lỗi tạm thời (429/5xx).

    Credential lấy per-request qua current_creds() (auth/bearer truyền vào từng call).
    POST không idempotent (create_relation, create_work_package, log_time, add_comment,
    add_member...) → KHÔNG retry để tránh tạo trùng khi mất phản hồi sau khi đã ghi thành công.
    GET/PATCH/DELETE/PUT idempotent → vẫn retry như cũ.
    """
    creds = current_creds()
    c = _client(creds.base_url)
    auth_kwargs = _request_kwargs(creds)
    r = c.request(method, path, params=params, json=body, **auth_kwargs)
    if r.status_code in _RETRYABLE and method.upper() != "POST":
        # Retry-After có thể là số giây hoặc HTTP-date (RFC 7231); date → fallback 1s.
        try:
            retry_after = float(r.headers.get("Retry-After", "1") or 1)
        except ValueError:
            retry_after = 1.0
        log.warning("HTTP %s từ %s %s — retry sau %.1fs", r.status_code, method, path, retry_after)
        time.sleep(min(retry_after, 10))
        r = c.request(method, path, params=params, json=body, **auth_kwargs)
    if r.status_code == 401:
        raise RuntimeError(
            "HTTP 401: API key không hợp lệ hoặc đã hết hạn. "
            "Tạo key mới tại My account → Access tokens → API."
        )
    if r.status_code == 403:
        raise RuntimeError(
            f"HTTP 403: tài khoản không đủ quyền cho thao tác này ({method} {path})."
        )
    if r.status_code == 404:
        raise RuntimeError(f"HTTP 404: không tìm thấy {path}. {_error_message(r)}")
    if r.status_code == 409:
        raise ConflictError(f"HTTP 409: {_error_message(r)}")
    if r.status_code >= 400:
        raise RuntimeError(f"OpenProject trả về HTTP {r.status_code}: {_error_message(r)}")
    return r.json() if r.content else {}


def _collection(
    path: str,
    filters: list | None = None,
    page_size: int = 25,
    offset: int = 1,
    sort: list | None = None,
    extra_params: dict | None = None,
) -> dict:
    params: dict[str, Any] = {"pageSize": page_size, "offset": offset}
    if filters:
        params["filters"] = json.dumps(filters)
    if sort:
        params["sortBy"] = json.dumps(sort)
    if extra_params:
        params.update(extra_params)
    return _req("GET", path, params=params)


def patch_wp_with_lock(wp_id: int, body: dict, lock_version: int | None = None) -> dict:
    """PATCH work package với optimistic locking tự động (lấy lockVersion + retry 1 lần).

    lock_version=None → tự lấy lockVersion mới nhất qua GET. Gặp 409 (ai đó vừa sửa,
    hoặc rollup từ subtask/relation bump version cha) → lấy lại lockVersion và thử lại
    MỘT lần. Lần 409 thứ hai → ném ConflictError với hướng dẫn rõ ràng.

    Cảnh báo: retry tự động sẽ ghi đè thay đổi đồng thời của người khác xảy ra giữa hai
    lần thử — chấp nhận được khi chỉ một tác nhân (AI) đang ghi.
    """
    lv = lock_version
    if lv is None:
        lv = _req("GET", f"/work_packages/{wp_id}").get("lockVersion")
    payload = {**body, "lockVersion": lv}
    try:
        return _req("PATCH", f"/work_packages/{wp_id}", body=payload)
    except ConflictError:
        payload["lockVersion"] = _req("GET", f"/work_packages/{wp_id}").get("lockVersion")
        try:
            return _req("PATCH", f"/work_packages/{wp_id}", body=payload)
        except ConflictError as e:
            raise ConflictError(
                f"HTTP 409 sau khi thử lại: work package #{wp_id} bị sửa đồng thời liên tục. "
                "Lấy lại bằng get_work_package rồi thử update lại."
            ) from e
