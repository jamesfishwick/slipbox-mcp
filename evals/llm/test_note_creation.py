"""LLM eval: note creation workflow.

Tests that Claude correctly uses MCP tools to add knowledge to the slipbox.
Requires claude CLI to be installed and authenticated.
"""
import pytest
from evals.conftest import run_claude_eval


@pytest.mark.eval
class TestNoteCreation:

    def test_creates_note_with_relevant_tags(self, seeded_slipbox, test_config):
        """LLM should create a note with appropriate tags when asked to add knowledge."""
        svc, refs = seeded_slipbox

        result = run_claude_eval(
            prompt=(
                "Add a note about how Spinoza's conatus concept relates to Faggin's "
                "view that consciousness is fundamental to information processing. "
                "Tag it appropriately and link to any related existing notes."
            ),
            notes_dir=svc.repository.notes_dir,
            db_path=test_config.get_absolute_path(test_config.database_path),
        )
        assert result["exit_code"] == 0, f"claude failed: {result['stderr']}"

        # Grade: was at least one new note created?
        all_notes = svc.get_all_notes()
        existing_ids = set(refs.values())
        new_notes = [n for n in all_notes if n.id not in existing_ids]
        assert len(new_notes) >= 1, (
            f"Expected at least 1 new note, found {len(new_notes)}. "
            f"Total notes: {len(all_notes)}, seed notes: {len(existing_ids)}"
        )

        # Grade: does the new note have relevant tags?
        relevant_tags = {"panpsychism", "consciousness", "spinoza", "faggin",
                        "quantum", "conatus", "information", "philosophy-of-mind"}
        new_note = new_notes[0]
        tag_names = {t.name.lower() for t in new_note.tags}
        assert tag_names & relevant_tags, (
            f"Expected tags related to panpsychism/consciousness, got: {tag_names}"
        )

    def test_creates_links_to_existing_notes(self, seeded_slipbox, test_config):
        """LLM should link new notes to related existing notes."""
        svc, refs = seeded_slipbox

        result = run_claude_eval(
            prompt=(
                "Add a note about the combination problem in panpsychism. "
                "Connect it to my existing notes about panpsychism."
            ),
            notes_dir=svc.repository.notes_dir,
            db_path=test_config.get_absolute_path(test_config.database_path),
        )
        assert result["exit_code"] == 0, f"claude failed: {result['stderr']}"

        # Grade: new note exists and has outgoing links
        all_notes = svc.get_all_notes()
        existing_ids = set(refs.values())
        new_notes = [n for n in all_notes if n.id not in existing_ids]
        assert len(new_notes) >= 1, "Expected at least 1 new note"

        new_note = new_notes[0]
        linked = svc.get_linked_notes(new_note.id, "both")
        assert len(linked) >= 1, (
            f"Expected new note to be linked to existing notes, found {len(linked)} links"
        )

    def test_creates_literature_note_with_reference(self, seeded_slipbox, test_config):
        """LLM should create a literature note with citation when asked."""
        svc, refs = seeded_slipbox
        existing_ids = set(refs.values())

        result = run_claude_eval(
            prompt=(
                "Add a literature note about Chalmers' formulation of the hard "
                "problem from his book The Conscious Mind (1996). "
                "Include the citation as a reference."
            ),
            notes_dir=svc.repository.notes_dir,
            db_path=test_config.get_absolute_path(test_config.database_path),
        )
        assert result["exit_code"] == 0, f"claude failed: {result['stderr']}"

        # Grade: new note created
        all_notes = svc.get_all_notes()
        new_notes = [n for n in all_notes if n.id not in existing_ids]
        assert len(new_notes) >= 1, "Expected at least 1 new note"

        new_note = new_notes[0]

        # Grade: note type should be literature
        assert new_note.note_type.value == "literature", (
            f"Expected literature note type, got: {new_note.note_type.value}"
        )

        # Grade: references field should be populated
        assert len(new_note.references) >= 1, (
            f"Expected at least 1 reference, got: {new_note.references}"
        )

    def test_creates_fleeting_note(self, seeded_slipbox, test_config):
        """LLM should create a fleeting note when asked for a quick capture."""
        svc, refs = seeded_slipbox
        existing_ids = set(refs.values())

        result = run_claude_eval(
            prompt=(
                "Quick thought: there might be a connection between Russellian "
                "monism and Spinoza's dual-aspect theory. Capture this as a "
                "fleeting note for later processing."
            ),
            notes_dir=svc.repository.notes_dir,
            db_path=test_config.get_absolute_path(test_config.database_path),
        )
        assert result["exit_code"] == 0, f"claude failed: {result['stderr']}"

        # Grade: new note created
        all_notes = svc.get_all_notes()
        new_notes = [n for n in all_notes if n.id not in existing_ids]
        assert len(new_notes) >= 1, "Expected at least 1 new note"

        new_note = new_notes[0]

        # Grade: note type should be fleeting
        assert new_note.note_type.value == "fleeting", (
            f"Expected fleeting note type, got: {new_note.note_type.value}"
        )

    def test_searches_before_creating(self, seeded_slipbox, test_config):
        """LLM should search existing notes and link to related ones."""
        svc, refs = seeded_slipbox
        existing_ids = set(refs.values())

        result = run_claude_eval(
            prompt=(
                "Add a new permanent note about how IIT's phi measure could serve "
                "as empirical evidence for panpsychism. Search for related existing "
                "notes first and link to them."
            ),
            notes_dir=svc.repository.notes_dir,
            db_path=test_config.get_absolute_path(test_config.database_path),
        )
        assert result["exit_code"] == 0, f"claude failed: {result['stderr']}"

        # Grade: new note created
        all_notes = svc.get_all_notes()
        new_notes = [n for n in all_notes if n.id not in existing_ids]
        assert len(new_notes) >= 1, "Expected at least 1 new note"

        # Grade: new note links to at least one existing related note
        new_note = new_notes[0]
        linked = svc.get_linked_notes(new_note.id, "both")
        linked_ids = {n.id for n in linked}
        related_ids = {
            refs["permanent_iit"],
            refs["permanent_faggin"],
            refs["structure_panpsychism"],
            refs["permanent_hard_problem"],
            refs["fleeting_iit_question"],
        }
        assert linked_ids & related_ids, (
            f"Expected links to existing IIT/panpsychism notes. "
            f"Linked to: {linked_ids}, expected overlap with: {related_ids}"
        )
