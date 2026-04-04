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
                "Add a note about how Seneca's letters relate to modern cognitive behavioral therapy. "
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
        relevant_tags = {"stoicism", "cbt", "philosophy", "psychology", "seneca",
                        "cognitive-behavioral-therapy", "therapy", "emotions"}
        new_note = new_notes[0]
        tag_names = {t.name.lower() for t in new_note.tags}
        assert tag_names & relevant_tags, (
            f"Expected tags related to stoicism/CBT, got: {tag_names}"
        )

    def test_creates_links_to_existing_notes(self, seeded_slipbox, test_config):
        """LLM should link new notes to related existing notes."""
        svc, refs = seeded_slipbox

        result = run_claude_eval(
            prompt=(
                "Add a note about Stoic mindfulness practices. "
                "Connect it to my existing notes about Stoicism."
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
