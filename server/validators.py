"""Kiểm tra quan hệ work package — hàm thuần, chỉ dùng stdlib (test được không cần mạng).

Nguồn duy nhất của danh sách loại quan hệ hợp lệ (`RELATION_TYPES`) và logic chặn
quan hệ vô nghĩa/trùng/ngược trước khi gọi API.
"""

# Loại quan hệ hợp lệ của OpenProject (create_relation).
RELATION_TYPES = (
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

# Loại quan hệ có hướng phụ thuộc/lịch trình; chiều ngược giữa cùng cặp = vòng lặp trực tiếp.
_DIRECTIONAL = {"blocks", "blocked", "precedes", "follows"}


def _pair(a: object, b: object) -> frozenset[str]:
    """Cặp không thứ tự (so khớp quan hệ bất kể chiều)."""
    return frozenset({str(a), str(b)})


def validate_relation(
    from_id: int,
    to_id: int,
    relation_type: str,
    existing: list[dict],
) -> str | None:
    """Trả về chuỗi lỗi nếu quan hệ không hợp lệ, ngược lại None.

    Args:
        from_id: WP nguồn.
        to_id: WP đích.
        relation_type: loại quan hệ muốn tạo.
        existing: quan hệ hiện có của `from_id`, mỗi phần tử có khóa
            ``type``, ``from_id``, ``to_id``.
    """
    if relation_type not in RELATION_TYPES:
        return (
            f"relation_type không hợp lệ: {relation_type}. "
            f"Chọn một trong: {', '.join(RELATION_TYPES)}."
        )
    if str(from_id) == str(to_id):
        return f"Không thể tạo quan hệ từ #{from_id} tới chính nó (self-relation)."

    target = _pair(from_id, to_id)
    for rel in existing:
        r_from = str(rel.get("from_id"))
        r_to = str(rel.get("to_id"))
        if _pair(r_from, r_to) != target:
            continue
        # Cùng cặp WP. Nếu là quan hệ có hướng đang trỏ ngược lại → vòng lặp trực tiếp.
        if (
            relation_type in _DIRECTIONAL
            and rel.get("type") in _DIRECTIONAL
            and r_from == str(to_id)
            and r_to == str(from_id)
        ):
            return (
                f"Tạo quan hệ '{relation_type}' #{from_id}→#{to_id} sẽ tạo vòng lặp trực tiếp: "
                f"đã có quan hệ '{rel.get('type')}' ngược chiều giữa #{to_id} và #{from_id}."
            )
        return (
            f"Đã có quan hệ giữa #{from_id} và #{to_id}; OpenProject tự quản nghịch đảo, "
            "chỉ tạo một chiều (dùng get_relations để xem)."
        )
    return None
