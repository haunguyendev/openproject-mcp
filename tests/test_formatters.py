"""Unit tests cho các hàm thuần (không cần mạng) trong server/formatters.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

from formatters import (  # noqa: E402
    _fmt_activity,
    _fmt_news,
    _fmt_notification,
    _fmt_wp,
    _href_id,
    _link_title,
    _parent_fields,
    iso8601_to_hours,
)


def test_iso8601_to_hours():
    assert iso8601_to_hours("PT2H") == 2.0
    assert iso8601_to_hours("PT1H30M") == 1.5
    assert iso8601_to_hours("PT45M") == 0.75
    assert iso8601_to_hours("PT0H") == 0.0
    assert iso8601_to_hours(None) == 0.0
    assert iso8601_to_hours("") == 0.0
    assert iso8601_to_hours("garbage") == 0.0


def test_href_id():
    obj = {"_links": {"assignee": {"href": "/api/v3/users/42"}}}
    assert _href_id(obj, "assignee") == "42"
    assert _href_id({}, "assignee") is None
    assert _href_id({"_links": {"assignee": None}}, "assignee") is None


def test_link_title():
    obj = {"_links": {"status": {"title": "In progress"}}}
    assert _link_title(obj, "status") == "In progress"
    assert _link_title({}, "status") is None
    assert _link_title({"_links": {"status": None}}, "status") is None


def test_fmt_wp():
    wp = {
        "id": 7,
        "subject": "Fix bug",
        "startDate": "2026-06-01",
        "dueDate": "2026-06-10",
        "percentageDone": 50,
        "lockVersion": 3,
        "_links": {
            "type": {"title": "Bug"},
            "status": {"title": "New"},
            "assignee": {"title": "Nam"},
        },
    }
    out = _fmt_wp(wp)
    assert out["id"] == 7
    assert out["subject"] == "Fix bug"
    assert out["type"] == "Bug"
    assert out["status"] == "New"
    assert out["assignee"] == "Nam"
    assert out["due_date"] == "2026-06-10"
    assert out["done_ratio"] == 50
    assert out["lock_version"] == 3
    assert out["url"].endswith("/work_packages/7")


def test_parent_fields_present():
    wp = {"_links": {"parent": {"href": "/api/v3/work_packages/1204", "title": "Epic X"}}}
    out = _parent_fields(wp)
    assert out["parent_id"] == 1204
    assert isinstance(out["parent_id"], int)
    assert out["parent_subject"] == "Epic X"


def test_parent_fields_root():
    # WP gốc: không có link parent (hoặc parent=None) → cả hai trường None.
    assert _parent_fields({}) == {"parent_id": None, "parent_subject": None}
    assert _parent_fields({"_links": {"parent": None}}) == {
        "parent_id": None,
        "parent_subject": None,
    }


def test_fmt_news():
    news = {
        "id": 12,
        "title": "Sprint 5 kickoff",
        "summary": "Bắt đầu sprint mới",
        "createdAt": "2026-06-07T09:00:00Z",
        "_links": {
            "project": {"title": "Website"},
            "author": {"title": "Nam"},
        },
    }
    out = _fmt_news(news)
    assert out["id"] == 12
    assert out["title"] == "Sprint 5 kickoff"
    assert out["summary"] == "Bắt đầu sprint mới"
    assert out["project"] == "Website"
    assert out["author"] == "Nam"
    assert out["created_at"] == "2026-06-07T09:00:00Z"
    assert out["url"].endswith("/news/12")


def test_fmt_activity_comment_and_change():
    comment = {
        "_type": "Activity::Comment",
        "id": 99,
        "comment": {"raw": "Đã xong phần login"},
        "createdAt": "2026-06-07T10:00:00Z",
        "version": 4,
        "_links": {"user": {"title": "Nam", "href": "/api/v3/users/33"}},
    }
    out = _fmt_activity(comment)
    assert out["type"] == "comment"
    assert out["comment"] == "Đã xong phần login"
    assert out["user"] == "Nam"
    assert out["user_id"] == "33"
    assert out["version"] == 4

    change = {"_type": "Activity", "id": 100, "comment": {"raw": ""}}
    assert _fmt_activity(change)["type"] == "change"


def test_fmt_notification():
    n = {
        "id": 5,
        "reason": "mentioned",
        "subject": "Bạn được nhắc tới trong #123",
        "readIAN": False,
        "createdAt": "2026-06-07T11:00:00Z",
        "_links": {
            "project": {"title": "Website"},
            "resource": {"title": "Fix login", "href": "/api/v3/work_packages/123"},
        },
    }
    out = _fmt_notification(n)
    assert out["id"] == 5
    assert out["reason"] == "mentioned"
    assert out["read"] is False
    assert out["project"] == "Website"
    assert out["resource"] == "Fix login"
    assert out["resource_url"].endswith("/api/v3/work_packages/123")
