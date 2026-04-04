"""Tests for shared formatting helpers."""
import datetime

from slipbox_mcp.formatting import (
    content_preview,
    format_cluster_summary,
    format_note_compact,
    format_note_detail,
    format_note_summary,
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


class TestContentPreview:
    def test_truncates_long_content(self):
        content = "a" * 200
        result = content_preview(content, max_len=150)
        assert len(result) == 153  # 150 + "..."
        assert result.endswith("...")

    def test_replaces_newlines(self):
        content = "line one\nline two\nline three"
        result = content_preview(content)
        assert "\n" not in result
        assert "line one line two line three" == result

    def test_short_content_unchanged(self):
        content = "short"
        result = content_preview(content)
        assert result == "short"

    def test_custom_max_len(self):
        content = "a" * 50
        result = content_preview(content, max_len=10)
        assert result == "a" * 10 + "..."


class TestFormatTagList:
    def test_tag_objects(self):
        tags = [Tag(name="alpha"), Tag(name="beta")]
        assert format_tag_list(tags) == "alpha, beta"

    def test_plain_strings(self):
        tags = ["alpha", "beta"]
        assert format_tag_list(tags) == "alpha, beta"

    def test_empty(self):
        assert format_tag_list([]) == ""


class TestFormatNoteSummary:
    def test_basic(self):
        note = make_note()
        result = format_note_summary(note, index=1)
        assert "1. Test Note (ID: 20250101T120000000000000)" in result
        assert "Tags: test, example" in result
        assert "Preview: Test content here" in result

    def test_with_extra_lines(self):
        note = make_note()
        result = format_note_summary(note, index=2, extra_lines=["Similarity: 0.85"])
        assert "2. Test Note" in result
        assert "Similarity: 0.85" in result

    def test_no_index(self):
        note = make_note()
        result = format_note_summary(note, index=0)
        assert result.startswith("Test Note (ID:")

    def test_no_tags(self):
        note = make_note(tags=[])
        result = format_note_summary(note, index=1)
        assert "Tags:" not in result

    def test_preview_length(self):
        note = make_note(content="x" * 200)
        result = format_note_summary(note, index=1, preview_len=100)
        assert "x" * 100 + "..." in result


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


class TestFormatNoteDetail:
    def test_includes_full_metadata(self):
        note = make_note(references=["Ahrens 2017", "https://example.com"])
        result = format_note_detail(note)
        assert "# Test Note" in result
        assert "ID: 20250101T120000000000000" in result
        assert "Type: permanent" in result
        assert "Created:" in result
        assert "Updated:" in result
        assert "Tags: test, example" in result
        assert "Ahrens 2017" in result
        assert "https://example.com" in result
        assert "Test content here" in result

    def test_no_tags_or_refs(self):
        note = make_note(tags=[], references=[])
        result = format_note_detail(note)
        assert "Tags:" not in result
        assert "References:" not in result


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
