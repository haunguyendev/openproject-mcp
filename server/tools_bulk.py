"""Tools: thao tác hàng loạt — cập nhật/tạo nhiều work package trong một lần gọi.

Cả hai tool đều "continue-on-error": lỗi một item không dừng các item còn lại; kết quả
trả về envelope {updated|created, failed, ok_count, fail_count, total} — phải đọc "failed".
"""

from typing import Any

from app import mcp
from bulk_helpers import summarize_bulk
from custom_fields import apply_custom_fields
from formatters import _fmt_wp, _out
from op_client import _req, patch_wp_with_lock
from resolvers import resolve_priority_id, resolve_status_id, resolve_type_id


@mcp.tool()
def bulk_update_work_packages(
    ids: list[int],
    status: str | None = None,
    status_id: int | None = None,
    priority: str | None = None,
    priority_id: int | None = None,
    assignee_id: int | None = None,
    due_date: str | None = None,
    done_ratio: int | None = None,
    parent_id: int | None = None,
) -> str:
    """Cập nhật CÙNG một bộ trường cho nhiều work package trong một lần gọi.

    Áp dụng các trường được cung cấp cho TẤT CẢ ids (vd đóng 12 việc:
    bulk_update_work_packages(ids=[1201,...,1212], status="Rejected")). Mỗi việc tự lấy
    lockVersion + tự retry 409 một lần (xem update_work_package). Lỗi ở một việc KHÔNG dừng
    các việc còn lại — đọc "failed" trong kết quả để biết việc nào lỗi và tại sao.

    Tên status/priority được tra MỘT lần ở đầu. KHÔNG truyền cả tên lẫn ID cho cùng một trường.

    Args:
        ids: Danh sách ID work package cần cập nhật.
        status: Tên trạng thái (vd "Rejected") — tra ID một lần.
        status_id: ID trạng thái (dùng thay cho status).
        priority: Tên độ ưu tiên — tra ID một lần.
        priority_id: ID độ ưu tiên (dùng thay cho priority).
        assignee_id: ID người được gán mới.
        due_date: Hạn chót mới, YYYY-MM-DD.
        done_ratio: % hoàn thành (0-100).
        parent_id: ID work package cha mới.
    """
    if status and status_id:
        raise ValueError("Chỉ truyền status HOẶC status_id, không cả hai.")
    if priority and priority_id:
        raise ValueError("Chỉ truyền priority HOẶC priority_id, không cả hai.")
    if status:
        status_id = resolve_status_id(status)
    if priority:
        priority_id = resolve_priority_id(priority)

    links: dict[str, Any] = {}
    if status_id:
        links["status"] = {"href": f"/api/v3/statuses/{status_id}"}
    if priority_id:
        links["priority"] = {"href": f"/api/v3/priorities/{priority_id}"}
    if assignee_id:
        links["assignee"] = {"href": f"/api/v3/users/{assignee_id}"}
    if parent_id:
        links["parent"] = {"href": f"/api/v3/work_packages/{parent_id}"}

    body: dict[str, Any] = {}
    if due_date is not None:
        body["dueDate"] = due_date
    if done_ratio is not None:
        body["percentageDone"] = done_ratio
    if links:
        body["_links"] = links
    if not body:
        raise ValueError(
            "Không có trường nào để cập nhật: cung cấp status/priority/assignee_id/"
            "due_date/done_ratio/parent_id."
        )

    succeeded: list = []
    failed: list = []
    for wp_id in ids:
        try:
            succeeded.append(_fmt_wp(patch_wp_with_lock(wp_id, body)))
        except Exception as e:
            failed.append({"id": wp_id, "error": str(e)})
    return _out(summarize_bulk("updated", succeeded, failed))


def _create_one(project: str, item: dict) -> dict:
    """Tạo một work package từ dict item; trả về wp thô (chưa rút gọn). Dùng nội bộ bulk_create."""
    subject = item.get("subject")
    if not subject:
        raise ValueError("Thiếu 'subject' bắt buộc.")
    type_id = item.get("type_id")
    priority_id = item.get("priority_id")
    if item.get("type") and type_id:
        raise ValueError("Item: chỉ truyền type HOẶC type_id, không cả hai.")
    if item.get("priority") and priority_id:
        raise ValueError("Item: chỉ truyền priority HOẶC priority_id, không cả hai.")
    if item.get("type"):
        type_id = resolve_type_id(item["type"], project)
    if item.get("priority"):
        priority_id = resolve_priority_id(item["priority"])

    body: dict[str, Any] = {
        "subject": subject,
        "description": {"format": "markdown", "raw": item.get("description", "")},
        "_links": {},
    }
    if item.get("start_date"):
        body["startDate"] = item["start_date"]
    if item.get("due_date"):
        body["dueDate"] = item["due_date"]
    if type_id:
        body["_links"]["type"] = {"href": f"/api/v3/types/{type_id}"}
    if item.get("assignee_id"):
        body["_links"]["assignee"] = {"href": f"/api/v3/users/{item['assignee_id']}"}
    if priority_id:
        body["_links"]["priority"] = {"href": f"/api/v3/priorities/{priority_id}"}
    if item.get("parent_id"):
        body["_links"]["parent"] = {"href": f"/api/v3/work_packages/{item['parent_id']}"}
    if item.get("custom_fields"):
        apply_custom_fields(body, item["custom_fields"])
    return _req("POST", f"/projects/{project}/work_packages", body=body)


@mcp.tool()
def bulk_create_work_packages(project: str, items: list[dict]) -> str:
    """Tạo nhiều work package PHẲNG trong một dự án, trong một lần gọi.

    Mỗi item là dict mô tả một việc; "subject" bắt buộc. parent_id (nếu có) phải trỏ tới
    work package ĐÃ TỒN TẠI (vd tạo 10 task dưới Epic #500) — KHÔNG tham chiếu việc khác tạo
    trong cùng lần gọi. Để dựng cây Epic→Story→Task có quan hệ chéo: tạo từng tầng rồi dùng
    id trả về làm parent_id cho tầng sau, thêm quan hệ bằng create_relation.

    Lỗi một item KHÔNG dừng các item còn lại — đọc "failed" (kèm index) để biết item nào lỗi.
    POST không tự retry (tránh tạo trùng) → lỗi mạng tạm thời = item đó thất bại, tạo lại riêng.

    Args:
        project: ID hoặc identifier của dự án (áp dụng cho mọi item).
        items: Danh sách dict; mỗi dict gồm subject (bắt buộc), description, type|type_id,
            priority|priority_id, assignee_id, due_date, start_date, parent_id, custom_fields.
    """
    created: list = []
    failed: list = []
    for i, item in enumerate(items):
        try:
            created.append(_fmt_wp(_create_one(project, item)))
        except Exception as e:
            failed.append({"index": i, "subject": item.get("subject"), "error": str(e)})
    return _out(summarize_bulk("created", created, failed))
