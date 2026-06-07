"""Tools: work packages — liệt kê, xem, tạo, cập nhật, bình luận."""

from typing import Any

from app import mcp
from custom_fields import apply_custom_fields, extract_custom_fields
from formatters import _fmt_activity, _fmt_wp, _out, _parent_fields
from op_client import _collection, _req, patch_wp_with_lock
from resolvers import resolve_priority_id, resolve_status_id, resolve_type_id
from validators import validate_include
from wp_helpers import _fetch_children, _fetch_relations


@mcp.tool()
def list_work_packages(
    project: str | None = None,
    status: str = "open",
    assignee_me: bool = False,
    assignee_id: int | None = None,
    type_id: int | None = None,
    version_id: int | None = None,
    search: str | None = None,
    due_within_days: int | None = None,
    page_size: int = 25,
    offset: int = 1,
) -> str:
    """Liệt kê/tìm kiếm work packages (task, bug, feature...) với nhiều bộ lọc.

    Args:
        project: ID hoặc identifier của dự án (để trống = mọi dự án).
        status: "open" (đang mở), "closed" (đã đóng), "all" (tất cả).
        assignee_me: True = chỉ việc được gán cho tôi.
        assignee_id: Lọc theo người được gán (bỏ qua nếu assignee_me=True).
        type_id: Lọc theo loại (Bug/Feature/Task — xem list_types(project)).
        version_id: Lọc theo version/sprint (xem list_versions).
        search: Từ khóa tìm trong tiêu đề.
        due_within_days: Chỉ việc có hạn trong N ngày tới (gồm cả đã quá hạn).
        page_size: Số kết quả mỗi trang (mặc định 25).
        offset: Trang (bắt đầu từ 1).
    """
    filters: list = []
    if status in ("open", "closed"):
        filters.append({"status": {"operator": "o" if status == "open" else "c", "values": []}})
    if assignee_me:
        filters.append({"assignee": {"operator": "=", "values": ["me"]}})
    elif assignee_id:
        filters.append({"assignee": {"operator": "=", "values": [str(assignee_id)]}})
    if type_id:
        filters.append({"type": {"operator": "=", "values": [str(type_id)]}})
    if version_id:
        filters.append({"version": {"operator": "=", "values": [str(version_id)]}})
    if search:
        filters.append({"subject": {"operator": "~", "values": [search]}})
    if due_within_days is not None:
        filters.append({"dueDate": {"operator": "<t+", "values": [str(due_within_days)]}})

    path = f"/projects/{project}/work_packages" if project else "/work_packages"
    data = _collection(path, filters, page_size, offset, sort=[["updatedAt", "desc"]])
    items = [_fmt_wp(w) for w in data.get("_embedded", {}).get("elements", [])]
    return _out({"total": data.get("total"), "count": len(items), "items": items})


@mcp.tool()
def get_work_package(wp_id: int, include: list[str] | None = None) -> str:
    """Xem chi tiết một work package: mô tả, cha (parent), lockVersion (cần cho update).

    Mặc định trả thông tin cơ bản + parent_id/parent_subject (None nếu là WP gốc). Dùng
    `include` để gộp thêm con và quan hệ trong MỘT lần gọi — khỏi phải gọi riêng
    list_children và get_relations.

    Args:
        wp_id: ID của work package.
        include: Phần mở rộng lấy kèm (để trống = chỉ cơ bản + parent). Hợp lệ:
            - "children": danh sách work package con (subtask), đầy đủ trường.
            - "relations": quan hệ (blocks/precedes/relates...) của work package.
            Truyền cả hai để lấy gộp. Giá trị lạ → lỗi liệt kê giá trị hợp lệ.
    """
    includes = validate_include(include)
    wp = _req("GET", f"/work_packages/{wp_id}")
    detail = _fmt_wp(wp)
    detail["description"] = (wp.get("description") or {}).get("raw")
    detail["estimated_time"] = wp.get("estimatedTime")
    detail["spent_time"] = wp.get("spentTime")
    detail["created_at"] = wp.get("createdAt")
    detail["updated_at"] = wp.get("updatedAt")
    detail.update(_parent_fields(wp))
    custom = extract_custom_fields(wp)
    if custom:
        detail["custom_fields"] = custom
    if "children" in includes:
        detail["children"] = _fetch_children(wp_id)
    if "relations" in includes:
        detail["relations"] = _fetch_relations(wp_id)
    return _out(detail)


@mcp.tool()
def list_activities(wp_id: int) -> str:
    """Liệt kê activity (bình luận và thay đổi) của một work package — cũ → mới.

    Dùng để xem lịch sử trao đổi/cập nhật của một việc.

    Args:
        wp_id: ID work package.
    """
    # /activities là collection KHÔNG phân trang → trả hết; pageSize/offset bị bỏ qua.
    data = _collection(f"/work_packages/{wp_id}/activities")
    items = [_fmt_activity(a) for a in data.get("_embedded", {}).get("elements", [])]
    return _out({"wp_id": wp_id, "total": data.get("total"), "activities": items})


@mcp.tool()
def create_work_package(
    project: str,
    subject: str,
    description: str = "",
    type: str | None = None,
    type_id: int | None = None,
    assignee_id: int | None = None,
    due_date: str | None = None,
    start_date: str | None = None,
    priority: str | None = None,
    priority_id: int | None = None,
    parent_id: int | None = None,
    custom_fields: dict | None = None,
) -> str:
    """Tạo work package mới trong một dự án.

    Nhận tên hoặc ID cho type/priority: truyền type="Epic" thay vì tra type_id.
    type theo tên tự lọc theo loại đã bật trong dự án (project-scoped, tránh 422).
    KHÔNG truyền đồng thời cả tên lẫn ID cho cùng một trường.

    Args:
        project: ID hoặc identifier của dự án.
        subject: Tiêu đề công việc.
        description: Mô tả (hỗ trợ markdown).
        type: Tên loại (vd "Epic", "Task") — tool tự tra ID theo loại đã bật trong dự án.
        type_id: ID loại (xem list_types(project)). Dùng thay cho type — để trống dùng mặc định.
        assignee_id: ID người được gán (xem list_project_members).
        due_date: Hạn chót, định dạng YYYY-MM-DD.
        start_date: Ngày bắt đầu, YYYY-MM-DD.
        priority: Tên độ ưu tiên (vd "High") — tool tự tra ID.
        priority_id: ID độ ưu tiên (xem list_priorities). Dùng thay cho priority.
        parent_id: ID work package cha (tạo subtask bên dưới nó).
        custom_fields: Custom field theo ID, vd {"1": "Foo", "2": 42}. Trường liên kết
            (user/version/list) truyền href, vd {"3": "/api/v3/users/14"}.
    """
    if type and type_id:
        raise ValueError("Chỉ truyền type HOẶC type_id, không cả hai.")
    if priority and priority_id:
        raise ValueError("Chỉ truyền priority HOẶC priority_id, không cả hai.")
    if type:
        type_id = resolve_type_id(type, project)
    if priority:
        priority_id = resolve_priority_id(priority)

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
    if parent_id:
        body["_links"]["parent"] = {"href": f"/api/v3/work_packages/{parent_id}"}
    if custom_fields:
        apply_custom_fields(body, custom_fields)

    wp = _req("POST", f"/projects/{project}/work_packages", body=body)
    return _out({"created": _fmt_wp(wp)})


@mcp.tool()
def update_work_package(
    wp_id: int,
    lock_version: int | None = None,
    subject: str | None = None,
    description: str | None = None,
    status: str | None = None,
    status_id: int | None = None,
    priority: str | None = None,
    priority_id: int | None = None,
    assignee_id: int | None = None,
    due_date: str | None = None,
    done_ratio: int | None = None,
    parent_id: int | None = None,
    custom_fields: dict | None = None,
) -> str:
    """Cập nhật work package (đổi trạng thái, độ ưu tiên, gán người, sửa hạn, đổi cha...).

    lock_version để trống → tool tự lấy lockVersion mới nhất. Nếu gặp xung đột 409
    (vd rollup từ subtask/relation bump version cha), tool tự lấy lại lockVersion và
    thử lại MỘT lần — bạn KHÔNG cần get_work_package thủ công trước khi gọi.
    Lưu ý: retry tự động có thể ghi đè thay đổi đồng thời của người khác giữa hai lần thử.

    Nhận tên hoặc ID cho status/priority: truyền status="In progress" thay vì status_id.
    KHÔNG truyền đồng thời cả tên lẫn ID cho cùng một trường.

    Args:
        wp_id: ID work package.
        lock_version: lockVersion hiện tại. Để trống = tool tự lấy + tự retry khi 409.
        subject: Tiêu đề mới.
        description: Mô tả mới (markdown).
        status: Tên trạng thái mới (vd "In progress") — tool tự tra ID.
        status_id: ID trạng thái mới (xem list_statuses). Dùng thay cho status.
        priority: Tên độ ưu tiên mới (vd "High") — tool tự tra ID.
        priority_id: ID độ ưu tiên mới (xem list_priorities). Dùng thay cho priority.
        assignee_id: ID người được gán mới.
        due_date: Hạn chót mới, YYYY-MM-DD.
        done_ratio: % hoàn thành (0-100).
        parent_id: ID work package cha mới (di chuyển task này thành subtask của nó).
        custom_fields: Custom field theo ID, vd {"1": "Foo", "2": 42}. Trường liên kết
            truyền href, vd {"3": "/api/v3/users/14"}.

    Đổi loại (type) không hỗ trợ ở đây — đặt type lúc tạo (create_work_package) hoặc đổi
    trên web, vì loại phụ thuộc dự án nên không tra theo tên an toàn ở update.
    """
    if status and status_id:
        raise ValueError("Chỉ truyền status HOẶC status_id, không cả hai.")
    if priority and priority_id:
        raise ValueError("Chỉ truyền priority HOẶC priority_id, không cả hai.")
    if status:
        status_id = resolve_status_id(status)
    if priority:
        priority_id = resolve_priority_id(priority)

    body: dict[str, Any] = {"_links": {}}
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
    if priority_id:
        body["_links"]["priority"] = {"href": f"/api/v3/priorities/{priority_id}"}
    if assignee_id:
        body["_links"]["assignee"] = {"href": f"/api/v3/users/{assignee_id}"}
    if parent_id:
        body["_links"]["parent"] = {"href": f"/api/v3/work_packages/{parent_id}"}
    if custom_fields:
        apply_custom_fields(body, custom_fields)
    if not body["_links"]:
        del body["_links"]

    wp = patch_wp_with_lock(wp_id, body, lock_version)
    return _out({"updated": _fmt_wp(wp)})


@mcp.tool()
def add_comment(wp_id: int, comment: str) -> str:
    """Thêm bình luận vào work package.

    Args:
        wp_id: ID work package.
        comment: Nội dung bình luận (markdown).
    """
    _req(
        "POST",
        f"/work_packages/{wp_id}/activities",
        body={"comment": {"format": "markdown", "raw": comment}},
    )
    return _out({"ok": True, "wp_id": wp_id})


@mcp.tool()
def delete_work_package(wp_id: int) -> str:
    """Xóa vĩnh viễn một work package (GHI/HỦY — cần xác nhận 2 lần).

    KHÔNG THỂ HOÀN TÁC: xóa cả subtask con và các quan hệ liên quan trong OpenProject.
    Để "ẩn mềm" thay vì xóa, hãy đổi trạng thái (vd Rejected/Closed) bằng update_work_package.

    Args:
        wp_id: ID của work package cần xóa.
    """
    _req("DELETE", f"/work_packages/{wp_id}")
    return _out({"removed": True, "wp_id": wp_id})
