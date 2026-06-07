"""Unit tests cho server/bulk_helpers.py::summarize_bulk — thuần, không cần mạng/mcp."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

from bulk_helpers import summarize_bulk  # noqa: E402


def test_partial_success_counts():
    out = summarize_bulk("updated", [{"id": 1}, {"id": 2}], [{"id": 3, "error": "boom"}])
    assert out["ok_count"] == 2
    assert out["fail_count"] == 1
    assert out["total"] == 3
    assert out["updated"] == [{"id": 1}, {"id": 2}]
    assert out["failed"] == [{"id": 3, "error": "boom"}]


def test_all_ok():
    out = summarize_bulk("created", [{"id": 1}], [])
    assert out["ok_count"] == 1
    assert out["fail_count"] == 0
    assert out["total"] == 1
    assert "created" in out


def test_all_fail():
    out = summarize_bulk("updated", [], [{"id": 9, "error": "x"}, {"id": 10, "error": "y"}])
    assert out["ok_count"] == 0
    assert out["fail_count"] == 2
    assert out["total"] == 2


def test_empty():
    out = summarize_bulk("updated", [], [])
    assert out["total"] == 0
    assert out["ok_count"] == out["fail_count"] == 0


def test_total_is_sum_invariant():
    out = summarize_bulk("created", [1, 2, 3], [4, 5])
    assert out["total"] == out["ok_count"] + out["fail_count"]
