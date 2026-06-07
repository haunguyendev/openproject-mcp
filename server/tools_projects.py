"""Tools: dự án, thành viên, và metadata (types/statuses/priorities)."""

from app import mcp
from config import BASE_URL
from formatters import _href_id, _link_title, _out
from op_client import _collection, _req


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
    return _out(
        {
            "id": me.get("id"),
            "name": me.get("name"),
            "login": me.get("login"),
            "email": me.get("email"),
            "admin": me.get("admin"),
        }
    )


@mcp.tool()
def list_types(project: str | None = None) -> str:
    """Liệt kê các loại work package (Task, Bug, Feature, Epic, User story...) kèm ID.

    Args:
        project: ID/identifier dự án (tùy chọn). Có giá trị → chỉ trả các loại **đã bật**
            trong dự án đó (tránh lỗi 422 khi tạo việc với loại chưa bật). Để trống →
            mọi loại toàn hệ thống. Khi sắp tạo việc trong một dự án cụ thể, nên truyền
            project để chọn đúng loại được phép.
    """
    path = f"/projects/{project}/types" if project else "/types"
    data = _req("GET", path)
    items = [
        {"id": t.get("id"), "name": t.get("name")}
        for t in data.get("_embedded", {}).get("elements", [])
    ]
    return _out(items)


@mcp.tool()
def list_statuses() -> str:
    """Liệt kê các trạng thái (New, In progress, Closed...) kèm ID."""
    data = _req("GET", "/statuses")
    items = [
        {"id": s.get("id"), "name": s.get("name"), "is_closed": s.get("isClosed")}
        for s in data.get("_embedded", {}).get("elements", [])
    ]
    return _out(items)


@mcp.tool()
def list_priorities() -> str:
    """Liệt kê các mức độ ưu tiên (Low, Normal, High...) kèm ID."""
    data = _req("GET", "/priorities")
    items = [
        {"id": p.get("id"), "name": p.get("name")}
        for p in data.get("_embedded", {}).get("elements", [])
    ]
    return _out(items)


@mcp.tool()
def list_versions(project: str) -> str:
    """Liệt kê các version/milestone/sprint của một dự án (kèm ID để lọc work package).

    Args:
        project: ID hoặc identifier của dự án.
    """
    data = _req("GET", f"/projects/{project}/versions")
    items = [
        {
            "id": v.get("id"),
            "name": v.get("name"),
            "status": v.get("status"),
            "start_date": v.get("startDate"),
            "due_date": v.get("dueDate"),
            "sharing": v.get("sharing"),
        }
        for v in data.get("_embedded", {}).get("elements", [])
    ]
    return _out({"total": data.get("total"), "items": items})
