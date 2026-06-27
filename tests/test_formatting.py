"""Tests for shared formatting helpers."""

import datetime

from slipbox_mcp.formatting import (
    format_cluster_summary,
    format_note_compact,
    format_tag_list,
)
from slipbox_mcp.models.schema import Note, NoteType, Tag


def make_note(**kwargs):
    defaults = dict(
        id="20250101T120000000000000",
        title="Test Note",
        content="Test content here",
        note_type=NoteType.PERMANENT,
        tags=[Tag(name="test"), Tag(name="example")],
        links=[],
        references=[],
        created_at=datetime.datetime(2025, 1, 1, 12, 0),
        updated_at=datetime.datetime(2025, 1, 1, 12, 0),
    )
    defaults.update(kwargs)
    return Note(**defaults)


class TestFormatTagList:
    def test_tag_objects(self):
        tags = [Tag(name="alpha"), Tag(name="beta")]
        assert format_tag_list(tags) == "alpha, beta"

    def test_plain_strings(self):
        tags = ["alpha", "beta"]
        assert format_tag_list(tags) == "alpha, beta"

    def test_empty(self):
        assert format_tag_list([]) == ""


class TestFormatNoteCompact:
    def test_basic(self):
        note = make_note()
        result = format_note_compact(note)
        assert "20250101T120" in result
        assert "Test Note" in result

    def test_with_tags(self):
        note = make_note()
        result = format_note_compact(note)
        assert "[test, example]" in result

    def test_no_tags(self):
        note = make_note(tags=[])
        result = format_note_compact(note)
        assert "[" not in result

    def test_max_three_tags(self):
        note = make_note(tags=[Tag(name=f"t{i}") for i in range(5)])
        result = format_note_compact(note)
        assert "t0, t1, t2" in result
        assert "t3" not in result


class TestFormatClusterSummary:
    def _make_cluster(self):
        class FakeCluster:
            id = "poetry-craft"
            suggested_title = "Poetry & Craft"
            score = 0.85
            note_count = 12
            orphan_count = 3
            tags = ["poetry", "craft", "revision"]
            notes = [
                {"id": "note1", "title": "Note One"},
                {"id": "note2", "title": "Note Two"},
            ]

        return FakeCluster()

    def test_basic(self):
        cluster = self._make_cluster()
        result = format_cluster_summary(cluster, index=1)
        assert "1. Poetry & Craft" in result
        assert "Score: 0.85" in result
        assert "Notes: 12" in result
        assert "Orphans: 3" in result
        assert "Tags: poetry, craft, revision" in result

    def test_include_notes(self):
        cluster = self._make_cluster()
        result = format_cluster_summary(cluster, index=1, include_notes=True)
        assert "Note One" in result
        assert "Note Two" in result

    def test_no_index(self):
        cluster = self._make_cluster()
        result = format_cluster_summary(cluster, index=0)
        assert result.startswith("Poetry & Craft")
