"""Tools quản trị (admin): users, roles, projects, memberships.

Các thao tác GHI ảnh hưởng trạng thái dùng chung — skill PHẢI tóm tắt payload và
được người dùng xác nhận trước; archive/remove cần xác nhận 2 lần. Thiếu quyền → HTTP 403.
"""

from typing import Any

from app import mcp
from config import BASE_URL
from formatters import _href_id, _link_title, _out
from op_client import _collection, _req


@mcp.tool()
def list_users(search: str | None = None, status: str = "active") -> str:
    """Liệt kê người dùng hệ thống (cần quyền admin).

    Args:
        search: Lọc theo tên (chứa từ khóa).
        status: active | registered | locked | invited.
    """
    filters: list = [{"status": {"operator": "=", "values": [status]}}]
    if search:
        filters.append({"name": {"operator": "~", "values": [search]}})
    data = _collection("/users", filters, page_size=100)
    items = [
        {
            "id": u.get("id"),
            "name": u.get("name"),
            "login": u.get("login"),
            "email": u.get("email"),
            "status": u.get("status"),
        }
        for u in data.get("_embedded", {}).get("elements", [])
    ]
    return _out({"total": data.get("total"), "items": items})


@mcp.tool()
def get_user(user_id: int) -> str:
    """Xem chi tiết một người dùng theo ID (cần quyền admin).

    Args:
        user_id: ID người dùng.
    """
    u = _req("GET", f"/users/{user_id}")
    return _out(
        {
            "id": u.get("id"),
            "name": u.get("name"),
            "login": u.get("login"),
            "email": u.get("email"),
            "status": u.get("status"),
            "admin": u.get("admin"),
        }
    )


@mcp.tool()
def list_roles() -> str:
    """Liệt kê các role (vai trò) để gán khi thêm thành viên."""
    data = _req("GET", "/roles")
    items = [
        {"id": r.get("id"), "name": r.get("name")}
        for r in data.get("_embedded", {}).get("elements", [])
    ]
    return _out(items)


@mcp.tool()
def create_project(
    name: str,
    identifier: str,
    description: str = "",
    parent_id: int | None = None,
    public: bool = False,
) -> str:
    """Tạo dự án mới (GHI — xác nhận trước khi gọi).

    Args:
        name: Tên hiển thị.
        identifier: Định danh URL (chữ thường, gạch nối, vd "my-project").
        description: Mô tả (markdown).
        parent_id: ID dự án cha (tạo dự án con).
        public: True = dự án công khai.
    """
    body: dict[str, Any] = {
        "name": name,
        "identifier": identifier,
        "active": True,
        "public": public,
        "description": {"format": "markdown", "raw": description},
        "_links": {},
    }
    if parent_id:
        body["_links"]["parent"] = {"href": f"/api/v3/projects/{parent_id}"}
    p = _req("POST", "/projects", body=body)
    return _out(
        {
            "created": {
                "id": p.get("id"),
                "identifier": p.get("identifier"),
                "name": p.get("name"),
                "url": f"{BASE_URL}/projects/{p.get('identifier')}",
            }
        }
    )


@mcp.tool()
def update_project(
    project: str,
    name: str | None = None,
    description: str | None = None,
    archive: bool = False,
) -> str:
    """Cập nhật hoặc LƯU TRỮ (archive) một dự án (GHI — archive cần xác nhận 2 lần).

    Args:
        project: ID hoặc identifier của dự án.
        name: Tên mới.
        description: Mô tả mới (markdown).
        archive: True = lưu trữ dự án (đặt active=false).
    """
    body: dict[str, Any] = {}
    if name is not None:
        body["name"] = name
    if description is not None:
        body["description"] = {"format": "markdown", "raw": description}
    if archive:
        body["active"] = False
    if not body:
        raise ValueError("Không có thay đổi nào: cung cấp name/description hoặc archive=True.")
    p = _req("PATCH", f"/projects/{project}", body=body)
    return _out(
        {
            "updated": {
                "id": p.get("id"),
                "identifier": p.get("identifier"),
                "name": p.get("name"),
                "active": p.get("active"),
            }
        }
    )


@mcp.tool()
def add_member(project: str, user_id: int, role_ids: list[int]) -> str:
    """Thêm một người dùng vào dự án với các role (GHI — xác nhận trước khi gọi).

    Args:
        project: ID hoặc identifier của dự án.
        user_id: ID người dùng (xem list_users).
        role_ids: Danh sách ID role (xem list_roles).
    """
    body: dict[str, Any] = {
        "_links": {
            "project": {"href": f"/api/v3/projects/{project}"},
            "principal": {"href": f"/api/v3/users/{user_id}"},
            "roles": [{"href": f"/api/v3/roles/{r}"} for r in role_ids],
        }
    }
    m = _req("POST", "/memberships", body=body)
    return _out(
        {
            "created": {
                "membership_id": m.get("id"),
                "user": _link_title(m, "principal"),
                "user_id": _href_id(m, "principal"),
                "roles": [r.get("title") for r in m.get("_links", {}).get("roles", [])],
            }
        }
    )


@mcp.tool()
def update_member(membership_id: int, role_ids: list[int]) -> str:
    """Đổi role của một thành viên (GHI — xác nhận trước khi gọi).

    Args:
        membership_id: ID membership (xem list_project_members trả về membership).
        role_ids: Danh sách ID role mới (xem list_roles).
    """
    body: dict[str, Any] = {"_links": {"roles": [{"href": f"/api/v3/roles/{r}"} for r in role_ids]}}
    m = _req("PATCH", f"/memberships/{membership_id}", body=body)
    return _out(
        {
            "updated": {
                "membership_id": m.get("id"),
                "roles": [r.get("title") for r in m.get("_links", {}).get("roles", [])],
            }
        }
    )


@mcp.tool()
def remove_member(membership_id: int) -> str:
    """Xóa một thành viên khỏi dự án (GHI/HỦY — cần xác nhận 2 lần).

    Args:
        membership_id: ID membership cần xóa.
    """
    _req("DELETE", f"/memberships/{membership_id}")
    return _out({"removed": True, "membership_id": membership_id})
