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

    def test_length_bound_matches_model(self):
        # The repo-layer pattern must enforce the same 1..255 bound as the
        # schema validator, or the two layers disagree on over-long ids.
        assert _is_safe_note_id("a" * 255) is True
        assert _is_safe_note_id("a" * 256) is False


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

    def test_model_rejects_overlong_id(self):
        with pytest.raises(ValidationError):
            Note(id="a" * 256, title="t", content="c")
        assert Note(id="a" * 255, title="t", content="c").id == "a" * 255


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

    def test_create_refuses_absolute_id_and_writes_nothing(self, note_repository):
        # The worst case: Path(notes_dir) / "/abs/x.md" discards notes_dir
        # entirely (operand discard). Use an absolute path inside the temp tree.
        target = note_repository.notes_dir.parent / "abs_create_payload"
        with pytest.raises(ValueError):
            note_repository.create(_smuggled_note(str(target)))
        assert not target.parent.joinpath("abs_create_payload.md").exists()

    def test_update_refuses_unsafe_id_and_overwrites_nothing(self, note_repository):
        # The highest-stakes path: a smuggled traversal id must not clobber a
        # file outside the notes dir. Assert no side effect, not merely a raise.
        victim = note_repository.notes_dir.parent / "update_victim.md"
        victim.write_text("original")
        with pytest.raises(ValueError):
            note_repository.update(_smuggled_note("../update_victim"))
        assert victim.read_text() == "original", "update() wrote outside the notes dir"
        victim.unlink()

    def test_update_refuses_absolute_id(self, note_repository):
        target = note_repository.notes_dir.parent / "abs_update_payload"
        with pytest.raises(ValueError):
            note_repository.update(_smuggled_note(str(target)))
        assert not target.parent.joinpath("abs_update_payload.md").exists()

    @pytest.mark.parametrize("bad", ["../victim", None])  # None -> absolute, set below
    def test_delete_refuses_unsafe_id_and_deletes_nothing(self, note_repository, bad):
        outside = note_repository.notes_dir.parent / "victim.md"
        outside.write_text("do not delete me")
        delete_id = bad if bad is not None else str(note_repository.notes_dir.parent / "victim")
        with pytest.raises(ValueError):
            note_repository.delete(delete_id)
        assert outside.exists(), "delete() removed a file outside the notes dir"
        outside.unlink()

    def test_get_returns_none_for_unsafe_id(self, note_repository):
        # Plant a readable file just outside the notes dir.
        outside = note_repository.notes_dir.parent / "secret.md"
        outside.write_text("---\nid: secret\ntitle: Secret\n---\ntop secret")
        assert note_repository.get("../secret") is None
        assert note_repository.get(str(note_repository.notes_dir.parent / "secret")) is None
        outside.unlink()

    def test_symlink_with_valid_stem_resolving_outside_is_refused(self, note_repository):
        """A symlink INSIDE notes_dir with a valid-stem name pointing outside.

        The regex passes (``evil`` is a valid stem); only ``.resolve()`` +
        ``is_relative_to`` in _note_path catches the escape. Pins that guard so a
        refactor that drops it fails loudly.
        """
        import os
        secret = note_repository.notes_dir.parent / "symlink_secret.md"
        secret.write_text("---\nid: symlink_secret\ntitle: S\n---\nsecret")
        link = note_repository.notes_dir / "evil.md"
        try:
            os.symlink(secret, link)
        except (OSError, NotImplementedError):
            pytest.skip("symlinks not supported on this platform")
        with pytest.raises(ValueError):
            note_repository.get("evil")
        link.unlink()
        secret.unlink()

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

    def test_planted_absolute_id_file_is_skipped(self, note_repository):
        """The operand-discard vector via a planted file's absolute frontmatter id."""
        planted = note_repository.notes_dir / "seed_abs.md"
        planted.write_text(
            "---\nid: /tmp/abs_payload\ntitle: SeedAbs\ntype: permanent\n---\n\nbody\n"
        )
        note_repository.rebuild_index()
        from sqlalchemy import select
        from slipbox_mcp.models.db_models import DBNote
        with note_repository.session_factory() as session:
            ids = session.scalars(select(DBNote.id)).all()
        assert "/tmp/abs_payload" not in ids

    def test_unsafe_id_file_not_counted_as_indexable(self, note_repository):
        """Regression for the rebuild-thrash bug: an unsafe-id file the parser
        skips must NOT be counted as indexable, or db_count != indexable_count is
        permanently true and a full rebuild fires on every construction.
        """
        (note_repository.notes_dir / "bad.md").write_text(
            "---\nid: ../../tmp/payload\ntitle: Bad\n---\nbody\n"
        )
        note_repository.create(
            Note(id="20260624T000000000000009", title="Good", content="ok")
        )
        # Only the safe note counts; the parser-skipped file must not.
        assert note_repository._count_indexable_files() == 1
