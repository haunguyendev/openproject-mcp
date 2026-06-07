"""Unit tests cho server/custom_fields.py — thuần, không cần mạng/mcp."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

from custom_fields import apply_custom_fields, extract_custom_fields  # noqa: E402


def test_extract_scalar_and_link():
    wp = {
        "id": 1,
        "subject": "x",
        "customField1": "Foo",
        "customField2": 42,
        "_links": {
            "status": {"title": "New"},
            "customField3": {"href": "/api/v3/users/14", "title": "Nam"},
        },
    }
    out = extract_custom_fields(wp)
    assert out["customField1"] == "Foo"
    assert out["customField2"] == 42
    assert out["customField3"] == {"title": "Nam", "href": "/api/v3/users/14"}
    assert "status" not in out  # không phải custom field


def test_extract_multi_value_link():
    wp = {
        "id": 1,
        "_links": {
            "customField5": [
                {"href": "/api/v3/users/1", "title": "A"},
                {"href": "/api/v3/users/2", "title": "B"},
            ]
        },
    }
    out = extract_custom_fields(wp)
    assert out["customField5"] == [
        {"title": "A", "href": "/api/v3/users/1"},
        {"title": "B", "href": "/api/v3/users/2"},
    ]


def test_extract_empty():
    assert extract_custom_fields({"id": 1, "_links": {"status": {"title": "New"}}}) == {}


def test_apply_scalar():
    body: dict = {}
    apply_custom_fields(body, {"1": "Foo", "2": 42})
    assert body["customField1"] == "Foo"
    assert body["customField2"] == 42
    assert "_links" not in body


def test_apply_link_dict_and_str():
    body: dict = {"_links": {}}
    apply_custom_fields(body, {"3": {"href": "/api/v3/users/14"}, "4": "/api/v3/versions/2"})
    assert body["_links"]["customField3"] == {"href": "/api/v3/users/14"}
    assert body["_links"]["customField4"] == {"href": "/api/v3/versions/2"}


def test_apply_key_normalization():
    body: dict = {}
    apply_custom_fields(body, {1: "a", "customField2": "b"})
    assert body["customField1"] == "a"
    assert body["customField2"] == "b"


def test_apply_invalid_key():
    with pytest.raises(ValueError):
        apply_custom_fields({}, {"foo": "bar"})
