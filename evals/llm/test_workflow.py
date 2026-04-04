"""LLM eval: multi-step knowledge workflows.

Tests that Claude can execute complex knowledge management workflows
involving multiple MCP tool calls. Requires claude CLI to be installed
and authenticated.
"""
import pytest
from evals.conftest import run_claude_eval


@pytest.mark.eval
class TestWorkflow:

    def test_knowledge_creation_workflow(self, seeded_slipbox, test_config):
        """LLM should create a note, tag it, and link to existing consciousness notes."""
        svc, refs = seeded_slipbox
        existing_ids = set(refs.values())

        result = run_claude_eval(
            prompt=(
                "I just read that Tononi's IIT axioms imply consciousness is "
                "an intrinsic property of certain physical systems, not an "
                "emergent one. Process this into my slipbox with appropriate "
                "tags and links to related notes."
            ),
            notes_dir=svc.repository.notes_dir,
            db_path=test_config.get_absolute_path(test_config.database_path),
        )
        assert result["exit_code"] == 0, f"claude failed: {result['stderr']}"

        # Grade: at least one new note created
        all_notes = svc.get_all_notes()
        new_notes = [n for n in all_notes if n.id not in existing_ids]
        assert len(new_notes) >= 1, (
            f"Expected at least 1 new note, found {len(new_notes)}"
        )

        new_note = new_notes[0]

        # Grade: tagged with consciousness-related tags
        relevant_tags = {"consciousness", "iit", "tononi", "panpsychism",
                        "philosophy-of-mind", "intrinsic", "information"}
        tag_names = {t.name.lower() for t in new_note.tags}
        assert tag_names & relevant_tags, (
            f"Expected consciousness-related tags, got: {tag_names}"
        )

        # Grade: linked to at least one existing related note
        linked = svc.get_linked_notes(new_note.id, "both")
        linked_ids = {n.id for n in linked}
        related_note_ids = {
            refs["permanent_iit"],
            refs["permanent_faggin"],
            refs["structure_panpsychism"],
            refs["permanent_hard_problem"],
        }
        assert linked_ids & related_note_ids, (
            f"Expected link to existing consciousness notes. Linked to: {linked_ids}"
        )

    def test_finds_and_fills_gap(self, seeded_slipbox, test_config):
        """LLM should create a bridging note between panpsychism and Wittgenstein."""
        svc, refs = seeded_slipbox
        existing_ids = set(refs.values())

        result = run_claude_eval(
            prompt=(
                "I notice my slipbox has notes on panpsychism and Wittgenstein "
                "separately. Create a note that bridges these two areas, "
                "synthesizing how the private language argument bears on "
                "panpsychist claims about intrinsic experience."
            ),
            notes_dir=svc.repository.notes_dir,
            db_path=test_config.get_absolute_path(test_config.database_path),
        )
        assert result["exit_code"] == 0, f"claude failed: {result['stderr']}"

        # Grade: new bridging note created
        all_notes = svc.get_all_notes()
        new_notes = [n for n in all_notes if n.id not in existing_ids]
        assert len(new_notes) >= 1, (
            f"Expected at least 1 new bridging note, found {len(new_notes)}"
        )

        # Grade: the new note should link to at least one panpsychism note
        # AND/OR a Wittgenstein note
        bridge_note = new_notes[0]
        linked = svc.get_linked_notes(bridge_note.id, "both")
        linked_ids = {n.id for n in linked}

        panpsychism_ids = {
            refs["structure_panpsychism"],
            refs["permanent_faggin"],
            refs["permanent_hard_problem"],
            refs["permanent_russellian"],
        }
        wittgenstein_ids = {
            refs["structure_wittgenstein"],
            refs["permanent_private_language"],
        }

        has_panpsychism_link = bool(linked_ids & panpsychism_ids)
        has_wittgenstein_link = bool(linked_ids & wittgenstein_ids)

        assert has_panpsychism_link or has_wittgenstein_link, (
            f"Expected bridging note to link to panpsychism and/or Wittgenstein notes. "
            f"Linked to: {linked_ids}"
        )

    def test_structure_note_recognition(self, seeded_slipbox, test_config):
        """LLM should recognize the existing panpsychism structure note."""
        svc, refs = seeded_slipbox
        result = run_claude_eval(
            prompt=(
                "My notes about panpsychism could use better organization. "
                "Can you check if there's a structure note or cluster that "
                "organizes the panpsychism notes? What does it look like?"
            ),
            notes_dir=svc.repository.notes_dir,
            db_path=test_config.get_absolute_path(test_config.database_path),
        )
        assert result["exit_code"] == 0, f"claude failed: {result['stderr']}"

        # Grade: output should mention the existing Panpsychism Overview structure note
        output = result["output"].lower()
        assert "panpsychism overview" in output or "structure" in output, (
            f"Expected mention of the existing panpsychism structure note. "
            f"Output: {output[:500]}"
        )
