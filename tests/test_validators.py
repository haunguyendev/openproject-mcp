"""Unit tests cho server/validators.py — thuần, không cần mạng/mcp."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

from validators import RELATION_TYPES, validate_relation  # noqa: E402


def test_valid_relation_returns_none():
    assert validate_relation(1, 2, "relates", []) is None
    assert validate_relation(1, 2, "blocks", []) is None


def test_invalid_type_rejected():
    err = validate_relation(1, 2, "bogus", [])
    assert err is not None
    assert "bogus" in err


def test_self_relation_rejected():
    err = validate_relation(5, 5, "relates", [])
    assert err is not None
    assert "self-relation" in err


def test_duplicate_same_direction_rejected():
    existing = [{"type": "relates", "from_id": "1", "to_id": "2"}]
    err = validate_relation(1, 2, "relates", existing)
    assert err is not None
    assert "Đã có quan hệ" in err


def test_duplicate_reverse_direction_rejected():
    # Quan hệ không-hướng tồn tại ở chiều ngược → vẫn coi là trùng cặp.
    existing = [{"type": "relates", "from_id": "2", "to_id": "1"}]
    err = validate_relation(1, 2, "relates", existing)
    assert err is not None
    assert "Đã có quan hệ" in err


def test_direct_cycle_blocks_rejected():
    # #2 đã blocks #1; tạo #1 blocks #2 → vòng lặp trực tiếp.
    existing = [{"type": "blocks", "from_id": "2", "to_id": "1"}]
    err = validate_relation(1, 2, "blocks", existing)
    assert err is not None
    assert "vòng lặp" in err


def test_direct_cycle_precedes_rejected():
    existing = [{"type": "precedes", "from_id": "2", "to_id": "1"}]
    err = validate_relation(1, 2, "precedes", existing)
    assert err is not None
    assert "vòng lặp" in err


def test_cross_type_same_pair_rejected():
    # Quyết định YAGNI của plan: một quan hệ mỗi cặp. relates sẵn có + thêm blocks → trùng.
    existing = [{"type": "relates", "from_id": "1", "to_id": "2"}]
    err = validate_relation(1, 2, "blocks", existing)
    assert err is not None
    assert "Đã có quan hệ" in err


def test_same_direction_directional_duplicate_rejected():
    # #1 blocks #2 đã tồn tại; tạo lại cùng chiều → trùng (không phải vòng lặp).
    existing = [{"type": "blocks", "from_id": "1", "to_id": "2"}]
    err = validate_relation(1, 2, "blocks", existing)
    assert err is not None
    assert "Đã có quan hệ" in err


def test_unrelated_pair_allows():
    existing = [{"type": "blocks", "from_id": "1", "to_id": "9"}]
    assert validate_relation(1, 2, "blocks", existing) is None


def test_ids_compared_across_int_and_str():
    existing = [{"type": "relates", "from_id": 1, "to_id": 2}]
    assert validate_relation(1, 2, "relates", existing) is not None


def test_relation_types_count():
    assert len(RELATION_TYPES) == 11
