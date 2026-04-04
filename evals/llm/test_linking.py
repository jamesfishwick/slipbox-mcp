"""LLM eval: link creation and deduplication workflows.

Tests that Claude correctly creates links between notes and avoids duplicates.
Requires claude CLI to be installed and authenticated.
"""
import pytest
from evals.conftest import run_claude_eval


@pytest.mark.eval
class TestLinking:

    def test_creates_bidirectional_link(self, seeded_slipbox, test_config):
        """LLM should create a contradicts link between private language and hard problem."""
        svc, refs = seeded_slipbox

        # The seed data already has a contradicts link from private_language -> hard_problem.
        # Ask for a link "between them" -- the LLM should recognize it exists
        # or create the reverse direction. Either way, a link should exist.
        result = run_claude_eval(
            prompt=(
                "The note about Wittgenstein's private language argument and the "
                "note about the hard problem of consciousness are in tension. "
                "Create a contradicts link between them if one doesn't exist already."
            ),
            notes_dir=svc.repository.notes_dir,
            db_path=test_config.get_absolute_path(test_config.database_path),
        )
        assert result["exit_code"] == 0, f"claude failed: {result['stderr']}"

        # Grade: a link should exist between private language and hard problem
        private_language_id = refs["permanent_private_language"]
        hard_problem_id = refs["permanent_hard_problem"]
        pl_linked = svc.get_linked_notes(private_language_id, "both")
        linked_ids = {n.id for n in pl_linked}
        assert hard_problem_id in linked_ids, (
            "Expected a link between private language and hard problem notes. "
            f"Private language linked to: {linked_ids}"
        )

    def test_does_not_duplicate_existing_link(self, seeded_slipbox, test_config):
        """LLM should recognize an existing link and not create a duplicate."""
        svc, refs = seeded_slipbox

        # Count links on panpsychism overview before
        panpsychism_id = refs["structure_panpsychism"]
        links_before = svc.get_linked_notes(panpsychism_id, "both")
        link_count_before = len(links_before)

        result = run_claude_eval(
            prompt=(
                "Connect the panpsychism overview note to Faggin's quantum "
                "information panpsychism note. Make sure there's a link between them."
            ),
            notes_dir=svc.repository.notes_dir,
            db_path=test_config.get_absolute_path(test_config.database_path),
        )
        assert result["exit_code"] == 0, f"claude failed: {result['stderr']}"

        # Grade: link count should not increase (link already exists)
        links_after = svc.get_linked_notes(panpsychism_id, "both")
        link_count_after = len(links_after)
        assert link_count_after <= link_count_before + 1, (
            f"Expected no duplicate link. Links before: {link_count_before}, "
            f"after: {link_count_after}"
        )
