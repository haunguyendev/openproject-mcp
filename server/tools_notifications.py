"""Tools: notification cá nhân — xem thông báo chưa đọc và đánh dấu đã đọc.

Cần OpenProject đủ mới (~12.1+); bản cũ không có endpoint /notifications → HTTP 404.
"""

from app import mcp
from formatters import _fmt_notification, _out
from op_client import _collection, _req


@mcp.tool()
def list_notifications(unread_only: bool = True, page_size: int = 25, offset: int = 1) -> str:
    """Liệt kê thông báo (notification) của chính tôi — mới nhất trước.

    Args:
        unread_only: True (mặc định) = chỉ thông báo chưa đọc.
        page_size: Số kết quả mỗi trang (mặc định 25).
        offset: Trang (bắt đầu từ 1).
    """
    filters = [{"readIAN": {"operator": "=", "values": ["f"]}}] if unread_only else None
    data = _collection("/notifications", filters, page_size, offset, sort=[["id", "desc"]])
    items = [_fmt_notification(n) for n in data.get("_embedded", {}).get("elements", [])]
    return _out({"total": data.get("total"), "count": len(items), "items": items})


@mcp.tool()
def mark_notification_read(notification_id: int) -> str:
    """Đánh dấu một thông báo là đã đọc.

    Args:
        notification_id: ID thông báo (xem list_notifications).
    """
    _req("POST", f"/notifications/{notification_id}/read_ian")
    return _out({"ok": True, "notification_id": notification_id, "read": True})
