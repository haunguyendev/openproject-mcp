"""Unit tests cho các hàm thuần (không cần mạng) trong server/formatters.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

from formatters import _fmt_news, _fmt_wp, _href_id, _link_title, iso8601_to_hours  # noqa: E402


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
