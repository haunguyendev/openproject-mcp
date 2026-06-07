"""Unit tests cho server/resolvers.py::match_by_name — thuần, không cần mạng/mcp."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

from resolvers import match_by_name  # noqa: E402

ITEMS = [{"id": 1, "name": "New"}, {"id": 7, "name": "In progress"}, {"id": 12, "name": "Closed"}]


def test_exact_match_returns_id():
    assert match_by_name("In progress", ITEMS, "status") == 7


def test_match_is_case_insensitive_and_trims():
    assert match_by_name("  in PROGRESS ", ITEMS, "status") == 7


def test_unknown_name_raises_with_options():
    with pytest.raises(ValueError) as e:
        match_by_name("Done", ITEMS, "status")
    msg = str(e.value)
    assert "Done" in msg
    assert "In progress" in msg  # liệt kê lựa chọn hợp lệ


def test_ambiguous_duplicate_names_rejected():
    dup = [{"id": 1, "name": "High"}, {"id": 2, "name": "high"}]
    with pytest.raises(ValueError) as e:
        match_by_name("High", dup, "priority")
    assert "mơ hồ" in str(e.value)


def test_empty_list_is_not_found():
    with pytest.raises(ValueError) as e:
        match_by_name("Epic", [], "type")
    assert "không tồn tại" in str(e.value)
