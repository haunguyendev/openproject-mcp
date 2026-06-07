"""Helpers rút gọn dữ liệu HAL+JSON của OpenProject thành JSON gọn cho Claude."""

import json
import re
from typing import Any

from config import BASE_URL


def iso8601_to_hours(value: str | None) -> float:
    """Chuyển ISO-8601 duration (vd 'PT1H30M') thành số giờ thập phân. None/lỗi → 0."""
    if not value or not value.startswith("PT"):
        return 0.0
    h = re.search(r"(\d+(?:\.\d+)?)H", value)
    m = re.search(r"(\d+(?:\.\d+)?)M", value)
    return (float(h.group(1)) if h else 0.0) + (float(m.group(1)) if m else 0.0) / 60


def _href_id(obj: dict, link: str) -> str | None:
    href = (obj.get("_links", {}).get(link) or {}).get("href")
    return href.rsplit("/", 1)[-1] if href else None


def _link_title(obj: dict, link: str) -> str | None:
    return (obj.get("_links", {}).get(link) or {}).get("title")


def _fmt_wp(wp: dict) -> dict:
    """Rút gọn work package thành các trường hữu ích."""
    return {
        "id": wp.get("id"),
        "subject": wp.get("subject"),
        "type": _link_title(wp, "type"),
        "status": _link_title(wp, "status"),
        "priority": _link_title(wp, "priority"),
        "assignee": _link_title(wp, "assignee"),
        "project": _link_title(wp, "project"),
        "start_date": wp.get("startDate"),
        "due_date": wp.get("dueDate"),
        "done_ratio": wp.get("percentageDone"),
        "lock_version": wp.get("lockVersion"),
        "url": f"{BASE_URL}/work_packages/{wp.get('id')}",
    }


def _fmt_news(n: dict) -> dict:
    """Rút gọn news (thông báo) thành các trường hữu ích."""
    return {
        "id": n.get("id"),
        "title": n.get("title"),
        "summary": n.get("summary"),
        "project": _link_title(n, "project"),
        "author": _link_title(n, "author"),
        "created_at": n.get("createdAt"),
        "url": f"{BASE_URL}/news/{n.get('id')}",
    }


def _out(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False, default=str)
