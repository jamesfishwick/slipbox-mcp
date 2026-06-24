"""Tests that deleting a note sweeps inbound references from referrers.

Regression coverage for the bug where delete() removed a note's own file and
DB row but left `[[id]]` wikilinks in the ## Links section of notes that
pointed at it. Because the filesystem is the source of truth and
rebuild_index re-parses ## Links from every file, those orphaned links were
resurrected into the DB on the next rebuild.
"""
from slipbox_mcp.models.schema import LinkType


class TestDeleteSweepsReferrers:
    """delete() must rewrite notes that link TO the deleted note."""

    def test_referrer_file_loses_dead_link(self, note_repository, zettel_service):
        """After deleting target, the referrer's markdown drops the [[target]] line."""
        target = zettel_service.create_note(
            title="Target Note",
            content="The note that will be deleted.",
        )
        referrer = zettel_service.create_note(
            title="Referrer Note",
            content="Points at the target.",
        )
        zettel_service.create_link(
            source_id=referrer.id,
            target_id=target.id,
            link_type=LinkType.EXTENDS,
            description="depends on target",
            bidirectional=True,
        )

        referrer_path = note_repository.notes_dir / f"{referrer.id}.md"
        assert f"[[{target.id}]]" in referrer_path.read_text()

        note_repository.delete(target.id)

        body = referrer_path.read_text()
        assert f"[[{target.id}]]" not in body, (
            "Referrer markdown still contains a link to the deleted note"
        )

    def test_rebuild_index_does_not_resurrect_link(self, note_repository, zettel_service):
        """The killer assertion: a rebuild must not bring the dead link back.

        This is what the demo exposed. Even if delete() cleaned the DB, the
        link lived on in the referrer's file and rebuild_index re-parsed it.
        """
        target = zettel_service.create_note(
            title="Target Note",
            content="Will be deleted.",
        )
        referrer = zettel_service.create_note(
            title="Referrer Note",
            content="Points at the target.",
        )
        zettel_service.create_link(
            source_id=referrer.id,
            target_id=target.id,
            link_type=LinkType.EXTENDS,
            bidirectional=True,
        )

        note_repository.delete(target.id)
        note_repository.rebuild_index()

        # No link in the DB should reference the deleted note as a target.
        from sqlalchemy import select
        from slipbox_mcp.models.db_models import DBLink
        with note_repository.session_factory() as session:
            dead = session.scalars(
                select(DBLink).where(DBLink.target_id == target.id)
            ).all()
        assert not dead, (
            f"rebuild_index resurrected {len(dead)} link(s) to the deleted note"
        )

    def test_live_links_survive_delete(self, note_repository, zettel_service):
        """Deleting one target must not strip the referrer's OTHER links."""
        target = zettel_service.create_note(title="Doomed", content="Goes away.")
        survivor = zettel_service.create_note(title="Survivor", content="Stays.")
        referrer = zettel_service.create_note(title="Referrer", content="Links to both.")

        zettel_service.create_link(
            source_id=referrer.id, target_id=target.id, link_type=LinkType.EXTENDS
        )
        zettel_service.create_link(
            source_id=referrer.id, target_id=survivor.id, link_type=LinkType.REFERENCE
        )

        note_repository.delete(target.id)

        body = (note_repository.notes_dir / f"{referrer.id}.md").read_text()
        assert f"[[{target.id}]]" not in body
        assert f"[[{survivor.id}]]" in body, "Deleting one target wrongly removed an unrelated link"
