"""Đọc/ghi custom field của work package — hàm thuần, chỉ stdlib (test được không cần mạng).

OpenProject biểu diễn custom field dạng `customFieldN`:
- Vô hướng (text/int/bool/date) → cấp cao nhất: `{"customField1": "Foo"}`.
- Liên kết (user/version/list) → trong `_links`: `{"_links": {"customField3": {"href": "..."}}}`.
"""

import re
from typing import Any

_CF_KEY = re.compile(r"^customField\d+$")


def _normalize_key(key: object) -> str:
    """Chuẩn hóa khóa custom field: 1 / "1" / "customField1" → "customField1"."""
    s = str(key)
    if _CF_KEY.match(s):
        return s
    if s.isdigit():
        return f"customField{s}"
    raise ValueError(f"Khóa custom field không hợp lệ: {key!r}. Dùng số ID hoặc 'customFieldN'.")


def extract_custom_fields(wp: dict) -> dict:
    """Gom mọi custom field từ một work package thành dict gọn.

    Vô hướng → giá trị trực tiếp; liên kết → {"title", "href"}.
    """
    out: dict[str, Any] = {}
    for k, v in wp.items():
        if _CF_KEY.match(k):
            out[k] = v
    for k, link in (wp.get("_links") or {}).items():
        if not _CF_KEY.match(k):
            continue
        if isinstance(link, list):
            # Custom field nhiều giá trị (list/multi-user) → mảng các liên kết.
            out[k] = [
                {"title": el.get("title"), "href": el.get("href")}
                for el in link
                if isinstance(el, dict)
            ]
        elif isinstance(link, dict):
            out[k] = {"title": link.get("title"), "href": link.get("href")}
    return out


def apply_custom_fields(body: dict, custom_fields: dict) -> None:
    """Ghi custom field vào body PATCH/POST (sửa body tại chỗ).

    Giá trị là dict → coi là liên kết, đặt vào `_links` nguyên trạng.
    Giá trị là chuỗi bắt đầu "/api/" → liên kết, bọc thành {"href": ...}.
    Còn lại → vô hướng, đặt ở cấp cao nhất.
    """
    for raw_key, value in custom_fields.items():
        key = _normalize_key(raw_key)
        if isinstance(value, dict):
            body.setdefault("_links", {})[key] = value
        elif isinstance(value, str) and value.startswith("/api/"):
            body.setdefault("_links", {})[key] = {"href": value}
        else:
            body[key] = value
