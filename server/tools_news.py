"""Tools: news (thông báo dự án) — liệt kê, xem, tạo, cập nhật, xóa.

News cần quyền "manage news" trong dự án. Thao tác GHI phải xác nhận trước;
delete cần xác nhận 2 lần. Thiếu quyền → HTTP 403.
"""

from typing import Any

from app import mcp
from formatters import _fmt_news, _out
from op_client import _collection, _req


@mcp.tool()
def list_news(project: str | None = None, page_size: int = 25, offset: int = 1) -> str:
    """Liệt kê news (thông báo) — mới nhất trước.

    Args:
        project: ID dự án (số) để lọc — bộ lọc news yêu cầu ID, không nhận identifier
            dạng chữ; để trống = mọi dự án.
        page_size: Số kết quả mỗi trang (mặc định 25).
        offset: Trang (bắt đầu từ 1).
    """
    filters = (
        [{"project_id": {"operator": "=", "values": [str(project)]}}] if project else None
    )
    data = _collection("/news", filters, page_size, offset, sort=[["created_at", "desc"]])
    items = [_fmt_news(n) for n in data.get("_embedded", {}).get("elements", [])]
    return _out({"total": data.get("total"), "count": len(items), "items": items})


@mcp.tool()
def get_news(news_id: int) -> str:
    """Xem chi tiết một news, gồm nội dung mô tả.

    Args:
        news_id: ID của news.
    """
    n = _req("GET", f"/news/{news_id}")
    detail = _fmt_news(n)
    detail["description"] = (n.get("description") or {}).get("raw")
    detail["updated_at"] = n.get("updatedAt")
    return _out(detail)


@mcp.tool()
def create_news(project: str, title: str, summary: str = "", description: str = "") -> str:
    """Tạo news (thông báo) mới trong một dự án (GHI — xác nhận trước khi gọi).

    Cần quyền "manage news" trong dự án.

    Args:
        project: ID hoặc identifier của dự án.
        title: Tiêu đề (tối đa 60 ký tự).
        summary: Tóm tắt ngắn (tối đa 255 ký tự).
        description: Nội dung (hỗ trợ markdown).
    """
    body: dict[str, Any] = {
        "title": title,
        "description": {"format": "markdown", "raw": description},
        "_links": {"project": {"href": f"/api/v3/projects/{project}"}},
    }
    if summary:
        body["summary"] = summary
    n = _req("POST", "/news", body=body)
    return _out({"created": _fmt_news(n)})


@mcp.tool()
def update_news(
    news_id: int,
    title: str | None = None,
    summary: str | None = None,
    description: str | None = None,
) -> str:
    """Cập nhật một news (GHI — xác nhận trước khi gọi).

    Args:
        news_id: ID của news.
        title: Tiêu đề mới (tối đa 60 ký tự).
        summary: Tóm tắt mới (tối đa 255 ký tự).
        description: Nội dung mới (markdown).
    """
    body: dict[str, Any] = {}
    if title is not None:
        body["title"] = title
    if summary is not None:
        body["summary"] = summary
    if description is not None:
        body["description"] = {"format": "markdown", "raw": description}
    if not body:
        raise ValueError("Không có thay đổi nào: cung cấp title/summary/description.")
    n = _req("PATCH", f"/news/{news_id}", body=body)
    return _out({"updated": _fmt_news(n)})


@mcp.tool()
def delete_news(news_id: int) -> str:
    """Xóa một news (GHI/HỦY — cần xác nhận 2 lần).

    Args:
        news_id: ID của news cần xóa.
    """
    _req("DELETE", f"/news/{news_id}")
    return _out({"removed": True, "news_id": news_id})
