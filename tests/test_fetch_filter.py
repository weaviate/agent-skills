"""Offline tests for skills/weaviate/scripts/fetch_filter.py filter parsing.

Run:  uv run --with weaviate-client==4.23.1 --with typer==0.21.0 --with pytest \
          pytest tests/ -q
No Weaviate cluster is required: only the JSON -> Filter translation is tested.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent / "skills" / "weaviate" / "scripts")
)

import fetch_filter as ff  # noqa: E402


def op_name(f):
    return f.operator.name if hasattr(f.operator, "name") else str(f.operator)


def test_no_filter_requested_returns_none():
    assert ff.parse_filters(None) is None
    assert ff.parse_filters("") is None
    assert ff.parse_filters("[]") is None


def test_simple_property_filter():
    f = ff.parse_filters('{"property":"year","operator":"greater_than","value":2020}')
    assert f.target == "year" and f.value == 2020
    assert "GREATER_THAN" in op_name(f)


def test_list_is_implicit_and_and_nesting_works():
    f = ff.parse_filters(
        '[{"property":"a","operator":"equal","value":1},'
        '{"operator":"or","filters":['
        '{"property":"b","operator":"equal","value":2},'
        '{"property":"c","operator":"like","value":"x*"}]}]'
    )
    assert "AND" in op_name(f)
    assert len(f.filters) == 2
    assert "OR" in op_name(f.filters[1])


def test_contains_none_is_supported():
    f = ff.parse_filters('{"property":"tags","operator":"contains_none","value":["a","b"]}')
    assert f.value == ["a", "b"]
    assert "CONTAINS_NONE" in op_name(f)


@pytest.mark.parametrize("raw,expected", [("true", True), ("false", False), ('"false"', False), ('"True"', True)])
def test_is_none_coerces_booleans_correctly(raw, expected):
    f = ff.parse_filters('{"property":"x","operator":"is_none","value":%s}' % raw)
    assert f.value is expected  # regression: bool("false") used to be True


@pytest.mark.parametrize(
    "raw",
    [
        '{"property":"c","operator":"equals","value":"x"}',  # typo'd operator
        '{"property":"c","operator":"equal"}',  # missing value
        '{"operator":"equal","value":1}',  # missing property
        '{"property":"c","value":1}',  # missing operator
        '"category=Science"',  # not an object
        "42",
        "{}",
        '{"operator":"and","filters":[]}',  # empty logical group
        '{"operator":"or"}',  # logical group without filters
        '{"property":"c","operator":"contains_any","value":"a"}',  # needs list
        '{"property":"c","operator":"is_none","value":"maybe"}',  # not a bool
        '{"operator":"and","filters":[{"property":"a","operator":"equal","value":1},'
        '{"property":"b","operator":"bogus","value":2}]}',  # one bad child
        "{not json",
    ],
)
def test_malformed_filters_fail_closed(raw):
    with pytest.raises(ff.FilterError):
        ff.parse_filters(raw)


def test_error_message_points_at_the_bad_clause():
    with pytest.raises(ff.FilterError) as ei:
        ff.parse_filters(
            '{"operator":"and","filters":[{"property":"a","operator":"equal","value":1},'
            '{"property":"b","operator":"bogus","value":2}]}'
        )
    assert "and[1]" in str(ei.value) and "bogus" in str(ei.value)
