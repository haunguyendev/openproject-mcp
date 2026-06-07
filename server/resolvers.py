"""Phân giải tên → ID cho status/type/priority (cho phép tool nhận tên thay vì ID).

`match_by_name` là hàm thuần (test được không cần mạng); các wrapper `resolve_*`
gọi API list tương ứng rồi giao cho `match_by_name`.
"""

from op_client import _req


def match_by_name(name: str, items: list[dict], kind: str) -> int:
    """Khớp `name` (không phân biệt hoa/thường, bỏ khoảng trắng đầu/cuối) với
    danh sách `[{id, name}]` → trả về id.

    0 khớp → ValueError kèm danh sách lựa chọn. >1 khớp (trùng tên) → ValueError 'mơ hồ'.

    Args:
        name: Tên cần khớp (vd "In progress", "Epic", "High").
        items: Danh sách mục, mỗi mục có khóa ``id`` và ``name``.
        kind: Nhãn loại để báo lỗi (vd "status", "type", "priority").
    """
    target = name.strip().casefold()
    matches = [it for it in items if (it.get("name") or "").strip().casefold() == target]
    if len(matches) == 1:
        return matches[0]["id"]
    options = ", ".join(it.get("name") or "" for it in items) or "(trống)"
    if not matches:
        raise ValueError(f"{kind} '{name}' không tồn tại. Lựa chọn: {options}.")
    raise ValueError(f"{kind} '{name}' mơ hồ (nhiều mục trùng tên). Lựa chọn: {options}.")


def _elements(data: dict) -> list[dict]:
    return [
        {"id": e.get("id"), "name": e.get("name")}
        for e in data.get("_embedded", {}).get("elements", [])
    ]


def resolve_status_id(name: str) -> int:
    """Tên trạng thái → ID (vd "In progress")."""
    return match_by_name(name, _elements(_req("GET", "/statuses")), "status")


def resolve_priority_id(name: str) -> int:
    """Tên độ ưu tiên → ID (vd "High")."""
    return match_by_name(name, _elements(_req("GET", "/priorities")), "priority")


def resolve_type_id(name: str, project: str | None = None) -> int:
    """Tên loại → ID (vd "Epic"). Có `project` → chỉ khớp loại đã bật trong dự án đó."""
    path = f"/projects/{project}/types" if project else "/types"
    return match_by_name(name, _elements(_req("GET", path)), "type")
