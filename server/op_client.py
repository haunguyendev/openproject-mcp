"""HTTP client + request helpers cho OpenProject API v3.

Auth: HTTP Basic, username "apikey", password = API token.
"""

import json
import time
from typing import Any

import httpx
from config import API_KEY, BASE_URL, TIMEOUT, log

_RETRYABLE = {429, 502, 503, 504}
_http: httpx.Client | None = None


class ConflictError(RuntimeError):
    """HTTP 409 (optimistic locking) — lockVersion đã cũ vì WP bị sửa đồng thời.

    Tách riêng để caller (patch_wp_with_lock) bắt chính xác và thử lại, thay vì
    nhận RuntimeError chung chung.
    """


def _client() -> httpx.Client:
    """Trả về HTTP client dùng chung (tái sử dụng kết nối)."""
    global _http
    if not BASE_URL:
        raise ValueError("OPENPROJECT_URL chưa được cấu hình trong .mcp.json.")
    if not API_KEY:
        raise ValueError(
            "OPENPROJECT_API_KEY chưa được cấu hình. Lấy key tại: "
            f"{BASE_URL}/my/access_token (My account → Access tokens → API)."
        )
    if _http is None or _http.is_closed:
        _http = httpx.Client(
            base_url=BASE_URL + "/api/v3",
            auth=("apikey", API_KEY),
            timeout=TIMEOUT,
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

    POST không idempotent (create_relation, create_work_package, log_time, add_comment,
    add_member...) → KHÔNG retry để tránh tạo trùng khi mất phản hồi sau khi đã ghi thành công.
    GET/PATCH/DELETE/PUT idempotent → vẫn retry như cũ.
    """
    c = _client()
    r = c.request(method, path, params=params, json=body)
    if r.status_code in _RETRYABLE and method.upper() != "POST":
        # Retry-After có thể là số giây hoặc HTTP-date (RFC 7231); date → fallback 1s.
        try:
            retry_after = float(r.headers.get("Retry-After", "1") or 1)
        except ValueError:
            retry_after = 1.0
        log.warning("HTTP %s từ %s %s — retry sau %.1fs", r.status_code, method, path, retry_after)
        time.sleep(min(retry_after, 10))
        r = c.request(method, path, params=params, json=body)
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
