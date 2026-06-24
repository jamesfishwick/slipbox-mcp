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
        pruned = note_repository.prune_dangling_links()
        assert (referrer_id, target_id, "extends") in pruned
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
