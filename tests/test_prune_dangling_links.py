"""Tests for dangling-link detection and pruning.

Covers the corpus-cleanup path: stubs left in ## Links sections by deletes
that predate referrer-sweeping, or by hand-editing. find_dangling_links is
read-only; prune_dangling_links rewrites affected notes.
"""
from slipbox_mcp.models.schema import LinkType


def _orphan_a_link(note_repository, zettel_service):
    """Create referrer->target link, then delete target's FILE only to
    simulate a pre-existing dangling stub (bypassing the new sweep)."""
    target = zettel_service.create_note(title="Target", content="goes away")
    referrer = zettel_service.create_note(title="Referrer", content="points")
    zettel_service.create_link(
        source_id=referrer.id,
        target_id=target.id,
        link_type=LinkType.EXTENDS,
    )
    # Remove the target file directly, leaving the stub in referrer's body.
    (note_repository.notes_dir / f"{target.id}.md").unlink()
    note_repository.rebuild_index()
    return referrer.id, target.id


class TestFindDanglingLinks:
    def test_detects_stub(self, note_repository, zettel_service):
        referrer_id, target_id = _orphan_a_link(note_repository, zettel_service)
        dangling = note_repository.find_dangling_links()
        assert (referrer_id, target_id, "extends") in dangling

    def test_clean_corpus_returns_empty(self, note_repository, zettel_service):
        a = zettel_service.create_note(title="A", content="a")
        b = zettel_service.create_note(title="B", content="b")
        zettel_service.create_link(source_id=a.id, target_id=b.id)
        assert note_repository.find_dangling_links() == []

    def test_find_is_read_only(self, note_repository, zettel_service):
        referrer_id, _ = _orphan_a_link(note_repository, zettel_service)
        before = (note_repository.notes_dir / f"{referrer_id}.md").read_text()
        note_repository.find_dangling_links()
        after = (note_repository.notes_dir / f"{referrer_id}.md").read_text()
        assert before == after, "find_dangling_links mutated a note"


class TestPruneDanglingLinks:
    def test_removes_stub_from_file(self, note_repository, zettel_service):
        referrer_id, target_id = _orphan_a_link(note_repository, zettel_service)
        pruned, failed = note_repository.prune_dangling_links()
        assert (referrer_id, target_id, "extends") in pruned
        assert failed == []
        body = (note_repository.notes_dir / f"{referrer_id}.md").read_text()
        assert f"[[{target_id}]]" not in body

    def test_survives_rebuild(self, note_repository, zettel_service):
        referrer_id, target_id = _orphan_a_link(note_repository, zettel_service)
        note_repository.prune_dangling_links()
        note_repository.rebuild_index()
        from sqlalchemy import select
        from slipbox_mcp.models.db_models import DBLink
        with note_repository.session_factory() as session:
            dead = session.scalars(
                select(DBLink).where(DBLink.target_id == target_id)
            ).all()
        assert not dead

    def test_preserves_live_links(self, note_repository, zettel_service):
        target = zettel_service.create_note(title="Doomed", content="x")
        survivor = zettel_service.create_note(title="Survivor", content="y")
        referrer = zettel_service.create_note(title="Ref", content="z")
        zettel_service.create_link(
            source_id=referrer.id, target_id=target.id, link_type=LinkType.EXTENDS
        )
        zettel_service.create_link(
            source_id=referrer.id, target_id=survivor.id, link_type=LinkType.REFERENCE
        )
        (note_repository.notes_dir / f"{target.id}.md").unlink()
        note_repository.rebuild_index()

        note_repository.prune_dangling_links()
        body = (note_repository.notes_dir / f"{referrer.id}.md").read_text()
        assert f"[[{target.id}]]" not in body
        assert f"[[{survivor.id}]]" in body

    def test_failed_update_reported_as_failed_not_pruned(
        self, note_repository, zettel_service, monkeypatch
    ):
        """A note whose rewrite throws must land in `failed`, never `pruned`.

        Regression guard: the original code appended to `pruned` before the
        write, so a failed update() was reported as a successful prune. The
        return value must never claim a prune that did not happen.
        """
        referrer_id, target_id = _orphan_a_link(note_repository, zettel_service)

        def boom(note):
            raise IOError("disk full")

        monkeypatch.setattr(note_repository, "update", boom)
        pruned, failed = note_repository.prune_dangling_links()

        assert (referrer_id, target_id, "extends") not in pruned
        assert (referrer_id, target_id, "extends") in failed
        # The stub is still on disk because the rewrite failed.
        body = (note_repository.notes_dir / f"{referrer_id}.md").read_text()
        assert f"[[{target_id}]]" in body

    def test_reports_multiple_dead_links_in_one_note(
        self, note_repository, zettel_service
    ):
        """One note linking to two deleted targets prunes both."""
        dead_a = zettel_service.create_note(title="Dead A", content="x")
        dead_b = zettel_service.create_note(title="Dead B", content="y")
        referrer = zettel_service.create_note(title="Ref", content="z")
        zettel_service.create_link(
            source_id=referrer.id, target_id=dead_a.id, link_type=LinkType.EXTENDS
        )
        zettel_service.create_link(
            source_id=referrer.id, target_id=dead_b.id, link_type=LinkType.REFERENCE
        )
        (note_repository.notes_dir / f"{dead_a.id}.md").unlink()
        (note_repository.notes_dir / f"{dead_b.id}.md").unlink()
        note_repository.rebuild_index()

        pruned, failed = note_repository.prune_dangling_links()
        assert failed == []
        assert (referrer.id, dead_a.id, "extends") in pruned
        assert (referrer.id, dead_b.id, "reference") in pruned
        body = (note_repository.notes_dir / f"{referrer.id}.md").read_text()
        assert f"[[{dead_a.id}]]" not in body
        assert f"[[{dead_b.id}]]" not in body

    def test_reports_actual_link_type(self, note_repository, zettel_service):
        """The reported link_type reflects the real link, not a hardcoded value."""
        target = zettel_service.create_note(title="Target", content="x")
        referrer = zettel_service.create_note(title="Ref", content="y")
        zettel_service.create_link(
            source_id=referrer.id, target_id=target.id, link_type=LinkType.CONTRADICTS
        )
        (note_repository.notes_dir / f"{target.id}.md").unlink()
        note_repository.rebuild_index()

        dangling = note_repository.find_dangling_links()
        assert (referrer.id, target.id, "contradicts") in dangling
