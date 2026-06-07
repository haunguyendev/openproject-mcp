# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "mcp>=1.2.0",
#     "httpx>=0.27",
# ]
# ///
"""OpenProject MCP server — quản lý công việc qua API v3.

Cấu hình qua biến môi trường (đặt trong .mcp.json của plugin):

  OPENPROJECT_URL              URL của OpenProject (vd: https://manage.promete.ai)
  OPENPROJECT_API_KEY          API key cá nhân (My account → Access tokens → API)
  OPENPROJECT_TIMEOUT_SECONDS  Timeout request (mặc định 30)

OpenProject API v3 xác thực bằng Basic Auth: username "apikey", password = API key.
"""

import json
import logging
import os
import sys
import time
from datetime import date
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

__version__ = "0.2.0"

BASE_URL = os.environ.get("OPENPROJECT_URL", "").rstrip("/")
API_KEY = os.environ.get("OPENPROJECT_API_KEY", "")
TIMEOUT = float(os.environ.get("OPENPROJECT_TIMEOUT_SECONDS", "30"))

# Log ra stderr — stdout dành riêng cho giao thức MCP (stdio transport).
logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                    format="%(asctime)s %(levelname)s openproject-mcp: %(message)s")
log = logging.getLogger(__name__)

mcp = FastMCP("openproject")

_RETRYABLE = {429, 502, 503, 504}
_http: httpx.Client | None = None


# ---------------------------------------------------------------- helpers

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


def _req(method: str, path: str, *, params: dict | None = None,
         body: dict | None = None) -> dict:
    """Gọi API với 1 lần retry cho lỗi tạm thời (429/5xx)."""
    c = _client()
    r = c.request(method, path, params=params, json=body)
    if r.status_code in _RETRYABLE:
        retry_after = float(r.headers.get("Retry-After", "1") or 1)
        log.warning("HTTP %s từ %s %s — retry sau %.1fs",
                    r.status_code, method, path, retry_after)
        time.sleep(min(retry_after, 10))
        r = c.request(method, path, params=params, json=body)
    if r.status_code == 401:
        raise RuntimeError(
            "HTTP 401: API key không hợp lệ hoặc đã hết hạn. "
            "Tạo key mới tại My account → Access tokens → API."
        )
    if r.status_code >= 400:
        raise RuntimeError(f"OpenProject trả về HTTP {r.status_code}: {_error_message(r)}")
    return r.json() if r.content else {}


def _href_id(obj: dict, link: str) -> str | None:
    href = (obj.get("_links", {}).get(link) or {}).get("href")
    return href.rsplit("/", 1)[-1] if href else None


def _link_title(obj: dict, link: str) -> str | None:
    return (obj.get("_links", {}).get(link) or {}).get("title")


def _fmt_wp(wp: dict) -> dict:
    """Rút gọn work package thành các trường hữu ích."""
    return {
        "id": wp.get("id"),
        "subject": wp.get("subject"),
        "type": _link_title(wp, "type"),
        "status": _link_title(wp, "status"),
        "priority": _link_title(wp, "priority"),
        "assignee": _link_title(wp, "assignee"),
        "project": _link_title(wp, "project"),
        "start_date": wp.get("startDate"),
        "due_date": wp.get("dueDate"),
        "done_ratio": wp.get("percentageDone"),
        "lock_version": wp.get("lockVersion"),
        "url": f"{BASE_URL}/work_packages/{wp.get('id')}",
    }


def _collection(path: str, filters: list | None = None, page_size: int = 25,
                offset: int = 1, sort: list | None = None,
                extra_params: dict | None = None) -> dict:
    params: dict[str, Any] = {"pageSize": page_size, "offset": offset}
    if filters:
        params["filters"] = json.dumps(filters)
    if sort:
        params["sortBy"] = json.dumps(sort)
    if extra_params:
        params.update(extra_params)
    return _req("GET", path, params=params)


def _out(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False, default=str)


# ---------------------------------------------------------------- work packages

@mcp.tool()
def list_work_packages(project: str | None = None, status: str = "open",
                       assignee_me: bool = False, search: str | None = None,
                       page_size: int = 25, offset: int = 1) -> str:
    """Liệt kê/tìm kiếm work packages (task, bug, feature...).

    Args:
        project: ID hoặc identifier của dự án (để trống = mọi dự án).
        status: "open" (đang mở), "closed" (đã đóng), "all" (tất cả).
        assignee_me: True = chỉ việc được gán cho tôi.
        search: Từ khóa tìm trong tiêu đề.
        page_size: Số kết quả mỗi trang (mặc định 25).
        offset: Trang (bắt đầu từ 1).
    """
    filters = []
    if status in ("open", "closed"):
        filters.append({"status": {"operator": "o" if status == "open" else "c", "values": []}})
    if assignee_me:
        filters.append({"assignee": {"operator": "=", "values": ["me"]}})
    if search:
        filters.append({"subject": {"operator": "~", "values": [search]}})

    path = f"/projects/{project}/work_packages" if project else "/work_packages"
    data = _collection(path, filters, page_size, offset,
                       sort=[["updatedAt", "desc"]])
    items = [_fmt_wp(w) for w in data.get("_embedded", {}).get("elements", [])]
    return _out({"total": data.get("total"), "count": len(items), "items": items})


@mcp.tool()
def get_work_package(wp_id: int) -> str:
    """Xem chi tiết một work package, gồm mô tả và lockVersion (cần cho update).

    Args:
        wp_id: ID của work package.
    """
    wp = _req("GET", f"/work_packages/{wp_id}")
    detail = _fmt_wp(wp)
    detail["description"] = (wp.get("description") or {}).get("raw")
    detail["estimated_time"] = wp.get("estimatedTime")
    detail["spent_time"] = wp.get("spentTime")
    detail["created_at"] = wp.get("createdAt")
    detail["updated_at"] = wp.get("updatedAt")
    return _out(detail)


@mcp.tool()
def create_work_package(project: str, subject: str, description: str = "",
                        type_id: int | None = None, assignee_id: int | None = None,
                        due_date: str | None = None, start_date: str | None = None,
                        priority_id: int | None = None) -> str:
    """Tạo work package mới trong một dự án.

    Args:
        project: ID hoặc identifier của dự án.
        subject: Tiêu đề công việc.
        description: Mô tả (hỗ trợ markdown).
        type_id: ID loại (xem list_types) — để trống dùng loại mặc định.
        assignee_id: ID người được gán (xem list_project_members).
        due_date: Hạn chót, định dạng YYYY-MM-DD.
        start_date: Ngày bắt đầu, YYYY-MM-DD.
        priority_id: ID độ ưu tiên.
    """
    body: dict[str, Any] = {
        "subject": subject,
        "description": {"format": "markdown", "raw": description},
        "_links": {},
    }
    if start_date:
        body["startDate"] = start_date
    if due_date:
        body["dueDate"] = due_date
    if type_id:
        body["_links"]["type"] = {"href": f"/api/v3/types/{type_id}"}
    if assignee_id:
        body["_links"]["assignee"] = {"href": f"/api/v3/users/{assignee_id}"}
    if priority_id:
        body["_links"]["priority"] = {"href": f"/api/v3/priorities/{priority_id}"}

    wp = _req("POST", f"/projects/{project}/work_packages", body=body)
    return _out({"created": _fmt_wp(wp)})


@mcp.tool()
def update_work_package(wp_id: int, lock_version: int, subject: str | None = None,
                        description: str | None = None, status_id: int | None = None,
                        assignee_id: int | None = None, due_date: str | None = None,
                        done_ratio: int | None = None) -> str:
    """Cập nhật work package (đổi trạng thái, gán người, sửa hạn...).

    Lấy lock_version mới nhất bằng get_work_package trước khi gọi.

    Args:
        wp_id: ID work package.
        lock_version: lockVersion hiện tại (chống ghi đè lẫn nhau).
        subject: Tiêu đề mới.
        description: Mô tả mới (markdown).
        status_id: ID trạng thái mới (xem list_statuses).
        assignee_id: ID người được gán mới.
        due_date: Hạn chót mới, YYYY-MM-DD.
        done_ratio: % hoàn thành (0-100).
    """
    body: dict[str, Any] = {"lockVersion": lock_version, "_links": {}}
    if subject is not None:
        body["subject"] = subject
    if description is not None:
        body["description"] = {"format": "markdown", "raw": description}
    if due_date is not None:
        body["dueDate"] = due_date
    if done_ratio is not None:
        body["percentageDone"] = done_ratio
    if status_id:
        body["_links"]["status"] = {"href": f"/api/v3/statuses/{status_id}"}
    if assignee_id:
        body["_links"]["assignee"] = {"href": f"/api/v3/users/{assignee_id}"}
    if not body["_links"]:
        del body["_links"]

    wp = _req("PATCH", f"/work_packages/{wp_id}", body=body)
    return _out({"updated": _fmt_wp(wp)})


@mcp.tool()
def add_comment(wp_id: int, comment: str) -> str:
    """Thêm bình luận vào work package.

    Args:
        wp_id: ID work package.
        comment: Nội dung bình luận (markdown).
    """
    _req("POST", f"/work_packages/{wp_id}/activities",
         body={"comment": {"format": "markdown", "raw": comment}})
    return _out({"ok": True, "wp_id": wp_id})


# ---------------------------------------------------------------- projects & members

@mcp.tool()
def list_projects(active_only: bool = True) -> str:
    """Liệt kê các dự án.

    Args:
        active_only: True = chỉ dự án đang hoạt động.
    """
    filters = [{"active": {"operator": "=", "values": ["t"]}}] if active_only else None
    data = _collection("/projects", filters, page_size=100)
    items = [
        {
            "id": p.get("id"),
            "identifier": p.get("identifier"),
            "name": p.get("name"),
            "active": p.get("active"),
            "url": f"{BASE_URL}/projects/{p.get('identifier')}",
        }
        for p in data.get("_embedded", {}).get("elements", [])
    ]
    return _out({"total": data.get("total"), "items": items})


@mcp.tool()
def list_project_members(project: str) -> str:
    """Liệt kê thành viên của một dự án (kèm user ID để gán việc).

    Args:
        project: ID của dự án (số, xem list_projects).
    """
    filters = [{"project": {"operator": "=", "values": [str(project)]}}]
    data = _collection("/memberships", filters, page_size=100)
    items = [
        {
            "user_id": _href_id(m, "principal"),
            "name": _link_title(m, "principal"),
            "roles": [r.get("title") for r in m.get("_links", {}).get("roles", [])],
        }
        for m in data.get("_embedded", {}).get("elements", [])
    ]
    return _out({"total": data.get("total"), "items": items})


@mcp.tool()
def whoami() -> str:
    """Xem thông tin tài khoản hiện tại (kiểm tra kết nối + lấy user ID của tôi)."""
    me = _req("GET", "/users/me")
    return _out({"id": me.get("id"), "name": me.get("name"),
                 "login": me.get("login"), "email": me.get("email")})


# ---------------------------------------------------------------- metadata

@mcp.tool()
def list_types() -> str:
    """Liệt kê các loại work package (Task, Bug, Feature...) kèm ID."""
    data = _req("GET", "/types")
    items = [{"id": t.get("id"), "name": t.get("name")}
             for t in data.get("_embedded", {}).get("elements", [])]
    return _out(items)


@mcp.tool()
def list_statuses() -> str:
    """Liệt kê các trạng thái (New, In progress, Closed...) kèm ID."""
    data = _req("GET", "/statuses")
    items = [{"id": s.get("id"), "name": s.get("name"), "is_closed": s.get("isClosed")}
             for s in data.get("_embedded", {}).get("elements", [])]
    return _out(items)


@mcp.tool()
def list_priorities() -> str:
    """Liệt kê các mức độ ưu tiên (Low, Normal, High...) kèm ID."""
    data = _req("GET", "/priorities")
    items = [{"id": p.get("id"), "name": p.get("name")}
             for p in data.get("_embedded", {}).get("elements", [])]
    return _out(items)


# ---------------------------------------------------------------- time tracking

@mcp.tool()
def log_time(wp_id: int, hours: float, spent_on: str | None = None,
             comment: str = "", activity_id: int | None = None) -> str:
    """Ghi nhận giờ làm việc (time entry) cho một work package.

    Args:
        wp_id: ID work package.
        hours: Số giờ (vd 1.5).
        spent_on: Ngày làm, YYYY-MM-DD (mặc định hôm nay).
        comment: Ghi chú.
        activity_id: ID loại hoạt động (để trống dùng mặc định).
    """
    body: dict[str, Any] = {
        "hours": f"PT{hours}H",
        "spentOn": spent_on or date.today().isoformat(),
        "comment": {"format": "markdown", "raw": comment},
        "_links": {"workPackage": {"href": f"/api/v3/work_packages/{wp_id}"}},
    }
    if activity_id:
        body["_links"]["activity"] = {"href": f"/api/v3/time_entries/activities/{activity_id}"}
    te = _req("POST", "/time_entries", body=body)
    return _out({"created": {"id": te.get("id"), "hours": te.get("hours"),
                             "spent_on": te.get("spentOn")}})


@mcp.tool()
def list_time_entries(project: str | None = None, user_me: bool = True,
                      from_date: str | None = None, to_date: str | None = None,
                      page_size: int = 50) -> str:
    """Xem các time entries đã ghi nhận.

    Args:
        project: ID dự án (để trống = mọi dự án).
        user_me: True = chỉ giờ của tôi.
        from_date: Từ ngày, YYYY-MM-DD.
        to_date: Đến ngày, YYYY-MM-DD.
        page_size: Số kết quả tối đa.
    """
    filters = []
    if user_me:
        filters.append({"user": {"operator": "=", "values": ["me"]}})
    if project:
        filters.append({"project": {"operator": "=", "values": [str(project)]}})
    if from_date and to_date:
        filters.append({"spentOn": {"operator": "<>d", "values": [from_date, to_date]}})

    data = _collection("/time_entries", filters, page_size)
    items = [
        {
            "id": t.get("id"),
            "hours": t.get("hours"),
            "spent_on": t.get("spentOn"),
            "work_package": _link_title(t, "workPackage"),
            "user": _link_title(t, "user"),
            "comment": (t.get("comment") or {}).get("raw"),
        }
        for t in data.get("_embedded", {}).get("elements", [])
    ]
    return _out({"total": data.get("total"), "items": items})


# ---------------------------------------------------------------- reports

@mcp.tool()
def report_overdue(project: str | None = None) -> str:
    """Báo cáo việc QUÁ HẠN: các work package đang mở có due date đã qua.

    Args:
        project: ID dự án (để trống = mọi dự án).
    """
    filters = [
        {"status": {"operator": "o", "values": []}},
        {"dueDate": {"operator": "<t-", "values": ["1"]}},
    ]
    path = f"/projects/{project}/work_packages" if project else "/work_packages"
    data = _collection(path, filters, page_size=100, sort=[["dueDate", "asc"]])
    items = [_fmt_wp(w) for w in data.get("_embedded", {}).get("elements", [])]
    return _out({"overdue_total": data.get("total"), "items": items})


@mcp.tool()
def report_my_tasks() -> str:
    """Báo cáo việc CỦA TÔI đang mở, sắp xếp theo hạn chót gần nhất."""
    filters = [
        {"status": {"operator": "o", "values": []}},
        {"assignee": {"operator": "=", "values": ["me"]}},
    ]
    data = _collection("/work_packages", filters, page_size=100,
                       sort=[["dueDate", "asc"]])
    items = [_fmt_wp(w) for w in data.get("_embedded", {}).get("elements", [])]
    today = date.today().isoformat()
    overdue = [i for i in items if i["due_date"] and i["due_date"] < today]
    return _out({"total_open": data.get("total"), "overdue_count": len(overdue),
                 "items": items})


@mcp.tool()
def report_project_progress(project: str) -> str:
    """Báo cáo tiến độ một dự án: tổng việc, mở/đóng, quá hạn, phân bố theo người.

    Args:
        project: ID hoặc identifier của dự án.
    """
    path = f"/projects/{project}/work_packages"
    all_data = _collection(path, page_size=1)
    open_data = _collection(path, [{"status": {"operator": "o", "values": []}}],
                            page_size=200)
    open_items = [_fmt_wp(w) for w in open_data.get("_embedded", {}).get("elements", [])]

    today = date.today().isoformat()
    by_assignee: dict[str, int] = {}
    overdue = 0
    for i in open_items:
        by_assignee[i["assignee"] or "(chưa gán)"] = by_assignee.get(i["assignee"] or "(chưa gán)", 0) + 1
        if i["due_date"] and i["due_date"] < today:
            overdue += 1

    total = all_data.get("total", 0)
    open_total = open_data.get("total", 0)
    return _out({
        "project": project,
        "total": total,
        "open": open_total,
        "closed": total - open_total,
        "overdue": overdue,
        "open_by_assignee": dict(sorted(by_assignee.items(), key=lambda x: -x[1])),
        "percent_closed": round((total - open_total) / total * 100, 1) if total else None,
    })


if __name__ == "__main__":
    log.info("openproject-mcp v%s — base_url=%s, api_key_set=%s",
             __version__, BASE_URL or "(chưa cấu hình)", bool(API_KEY))
    mcp.run()
