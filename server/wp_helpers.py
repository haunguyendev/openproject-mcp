"""Helpers chia sẻ để lấy con (children) và quan hệ (relations) của work package.

Tách khỏi tools_* để get_work_package, list_children, get_relations cùng tái dùng
(DRY) mà không import chéo giữa các module tool. Chỉ phụ thuộc formatters + op_client,
nên không tạo vòng import với các module tool.
"""

from formatters import _fmt_wp, _href_id, _link_title
from op_client import _collection, _req


def _fetch_relations(wp_id: int) -> list[dict]:
    """Lấy quan hệ của một WP, chuẩn hóa thành list dict (dùng chung tool + validator).

    Xin pageSize lớn để chắc chắn lấy hết: validator dựa trên danh sách này để chặn
    trùng/vòng lặp, nên danh sách bị cắt sẽ làm lọt kiểm tra.
    """
    data = _req("GET", f"/work_packages/{wp_id}/relations", params={"pageSize": 1000})
    items = []
    for r in data.get("_embedded", {}).get("elements", []):
        items.append(
            {
                "relation_id": r.get("id"),
                "type": r.get("type"),
                "to_id": _href_id(r, "to"),
                "to": _link_title(r, "to"),
                "from_id": _href_id(r, "from"),
                "description": r.get("description"),
            }
        )
    return items


def _fetch_children(wp_id: int) -> list[dict]:
    """Lấy work package con (subtask) của một WP → list _fmt_wp đầy đủ trường.

    Lọc theo parent; pageSize 100 đủ cho phần lớn cây con một cấp.
    """
    data = _collection(
        "/work_packages",
        [{"parent": {"operator": "=", "values": [str(wp_id)]}}],
        page_size=100,
    )
    return [_fmt_wp(w) for w in data.get("_embedded", {}).get("elements", [])]
