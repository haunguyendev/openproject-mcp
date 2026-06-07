"""Tools cho coder: subtask (children), quan hệ giữa work packages."""

from typing import Any

from app import mcp
from formatters import _fmt_wp, _href_id, _link_title, _out
from op_client import _collection, _req

_RELATION_TYPES = (
    "relates",
    "duplicates",
    "duplicated",
    "blocks",
    "blocked",
    "precedes",
    "follows",
    "includes",
    "partof",
    "requires",
    "required",
)


@mcp.tool()
def list_children(wp_id: int) -> str:
    """Liệt kê các work package con (subtask) của một work package.

    Args:
        wp_id: ID work package cha.
    """
    data = _collection(
        "/work_packages",
        [{"parent": {"operator": "=", "values": [str(wp_id)]}}],
        page_size=100,
    )
    items = [_fmt_wp(w) for w in data.get("_embedded", {}).get("elements", [])]
    return _out({"parent_id": wp_id, "total": data.get("total"), "children": items})


@mcp.tool()
def get_relations(wp_id: int) -> str:
    """Liệt kê quan hệ của một work package (blocks/blocked, precedes/follows, relates...).

    Args:
        wp_id: ID work package.
    """
    data = _req("GET", f"/work_packages/{wp_id}/relations")
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
    return _out({"wp_id": wp_id, "total": data.get("total"), "relations": items})


@mcp.tool()
def create_relation(
    from_id: int,
    to_id: int,
    relation_type: str = "relates",
    description: str = "",
) -> str:
    """Tạo quan hệ giữa hai work package (ghi — xác nhận trước khi gọi).

    Args:
        from_id: ID work package nguồn.
        to_id: ID work package đích.
        relation_type: Loại quan hệ: relates, blocks, blocked, precedes, follows,
            includes, partof, requires, required, duplicates, duplicated.
        description: Mô tả tùy chọn.
    """
    if relation_type not in _RELATION_TYPES:
        raise ValueError(
            f"relation_type không hợp lệ: {relation_type}. "
            f"Chọn một trong: {', '.join(_RELATION_TYPES)}."
        )
    body: dict[str, Any] = {
        "type": relation_type,
        "_links": {"to": {"href": f"/api/v3/work_packages/{to_id}"}},
    }
    if description:
        body["description"] = description
    r = _req("POST", f"/work_packages/{from_id}/relations", body=body)
    return _out(
        {
            "created": {
                "relation_id": r.get("id"),
                "type": r.get("type"),
                "from_id": from_id,
                "to_id": to_id,
            }
        }
    )
