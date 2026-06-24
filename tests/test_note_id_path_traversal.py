"""Security tests: note ids must not escape the notes directory.

A note id becomes a filename (``{id}.md``). Without constraint, a crafted id
like ``../../etc/passwd`` or ``/etc/shadow`` lets an MCP tool read, write, or
delete files outside the notes dir (Python's ``Path('/a') / '/etc/x'`` even
discards the left operand). These tests pin the two-layer defense:

1. ``Note.id`` validation rejects unsafe ids at the model boundary.
2. ``NoteRepository`` refuses unsafe ids at the filesystem boundary, so even an
   id that bypassed model validation (``Note.model_construct``) cannot touch a
   file outside the notes dir.
"""
import datetime

import pytest
from pydantic import ValidationError

from slipbox_mcp.models.schema import Note, NoteType
from slipbox_mcp.storage.note_repository import _is_safe_note_id


UNSAFE_IDS = [
    "../../etc/passwd",
    "../pwned",
    "/etc/shadow",
    "/tmp/pwned",
    "..",
    "foo/bar",
    "foo\\bar",
    "with space",
    "dot.in.id",
    "",
]

SAFE_IDS = [
    "20260101T000000000000001",          # generated format
    "20260624T123456789012abc",
    "manual-note_id",
    "ABC123",
]


class TestIdAlphabet:
    @pytest.mark.parametrize("bad", UNSAFE_IDS)
    def test_is_safe_note_id_rejects(self, bad):
        assert _is_safe_note_id(bad) is False

    @pytest.mark.parametrize("good", SAFE_IDS)
    def test_is_safe_note_id_accepts(self, good):
        assert _is_safe_note_id(good) is True

    def test_non_string_is_unsafe(self):
        assert _is_safe_note_id(None) is False
        assert _is_safe_note_id(123) is False


class TestModelBoundary:
    @pytest.mark.parametrize("bad", [i for i in UNSAFE_IDS if i])  # empty hits min_length too
    def test_model_rejects_unsafe_id(self, bad):
        with pytest.raises(ValidationError):
            Note(id=bad, title="t", content="c")

    def test_model_rejects_empty_id(self):
        with pytest.raises(ValidationError):
            Note(id="", title="t", content="c")

    @pytest.mark.parametrize("good", SAFE_IDS)
    def test_model_accepts_safe_id(self, good):
        note = Note(id=good, title="t", content="c")
        assert note.id == good

    def test_default_generated_id_is_safe(self):
        note = Note(title="t", content="c")
        assert _is_safe_note_id(note.id)


def _smuggled_note(bad_id: str) -> Note:
    """Build a Note carrying an unsafe id by bypassing model validation.

    model_construct skips validators, simulating an id that reached the
    repository despite the model-layer guard (the schema-violation hydration
    path uses model_construct). The filesystem layer must still refuse it.
    """
    now = datetime.datetime.now()
    return Note.model_construct(
        id=bad_id, title="t", content="c", note_type=NoteType.PERMANENT,
        tags=[], links=[], references=[], created_at=now, updated_at=now,
        metadata={},
    )


class TestFilesystemBoundary:
    @pytest.mark.parametrize("bad", ["../pwned_sentinel", "..", "foo/bar"])
    def test_create_refuses_unsafe_id_and_writes_nothing(self, note_repository, bad):
        outside = note_repository.notes_dir.parent / "pwned_sentinel.md"
        with pytest.raises(ValueError):
            note_repository.create(_smuggled_note(bad))
        assert not outside.exists(), "create() wrote a file outside the notes dir"

    def test_update_refuses_unsafe_id(self, note_repository):
        with pytest.raises(ValueError):
            note_repository.update(_smuggled_note("../escape"))

    def test_delete_refuses_unsafe_id_and_deletes_nothing(self, note_repository):
        # Plant a sentinel just outside the notes dir.
        outside = note_repository.notes_dir.parent / "victim.md"
        outside.write_text("do not delete me")
        with pytest.raises(ValueError):
            note_repository.delete("../victim")
        assert outside.exists(), "delete() removed a file outside the notes dir"
        outside.unlink()

    def test_get_returns_none_for_unsafe_id(self, note_repository):
        # Plant a readable file just outside the notes dir.
        outside = note_repository.notes_dir.parent / "secret.md"
        outside.write_text("---\nid: secret\ntitle: Secret\n---\ntop secret")
        assert note_repository.get("../secret") is None
        outside.unlink()

    def test_safe_roundtrip_still_works(self, note_repository):
        note = Note(id="20260624T000000000000001", title="Legit", content="ok")
        note_repository.create(note)
        got = note_repository.get(note.id)
        assert got is not None and got.title == "Legit"
        note_repository.delete(note.id)
        assert note_repository.get(note.id) is None


class TestRebuildIndexVector:
    def test_planted_traversal_id_file_is_skipped(self, note_repository):
        """A planted .md whose frontmatter id is a traversal stub must not index.

        This is the rebuild_index attack path: the parser refuses the hostile
        id before it can reach the model_construct fallback (which would bypass
        the validator and make the bad id writable on a later update()).
        """
        planted = note_repository.notes_dir / "seed.md"
        planted.write_text(
            "---\nid: ../../tmp/payload\ntitle: Seed\ntype: permanent\n---\n\nbody\n"
        )
        note_repository.rebuild_index()
        # The hostile note is not indexed...
        from sqlalchemy import select
        from slipbox_mcp.models.db_models import DBNote
        with note_repository.session_factory() as session:
            ids = session.scalars(select(DBNote.id)).all()
        assert "../../tmp/payload" not in ids
        # ...and nothing was written outside the notes dir.
        assert not (note_repository.notes_dir.parent / "tmp" / "payload.md").exists()
