"""LLM eval: knowledge exploration workflow.

Tests that Claude correctly explores the slipbox without creating new content.
Requires claude CLI to be installed and authenticated.
"""
import pytest
from evals.conftest import run_claude_eval


@pytest.mark.eval
class TestExploration:

    def test_explores_without_creating_notes(self, seeded_slipbox, test_config):
        """LLM should explore connections without creating new notes."""
        svc, refs = seeded_slipbox
        note_count_before = len(svc.get_all_notes())

        result = run_claude_eval(
            prompt=(
                "Explore what my slipbox knows about stoicism. "
                "Find connections and gaps. Do NOT create any new notes."
            ),
            notes_dir=svc.repository.notes_dir,
            db_path=test_config.get_absolute_path(test_config.database_path),
        )
        assert result["exit_code"] == 0, f"claude failed: {result['stderr']}"

        # Grade: no new notes created
        note_count_after = len(svc.get_all_notes())
        assert note_count_after == note_count_before, (
            f"Should not create notes during exploration. "
            f"Before: {note_count_before}, after: {note_count_after}"
        )

        # Grade: output mentions existing stoicism-related notes
        output = result["output"].lower()
        assert "stoic" in output or "seneca" in output or "marcus" in output, (
            "Exploration output should mention existing stoicism notes"
        )
