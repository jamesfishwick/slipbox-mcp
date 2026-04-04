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
                "Explore what my slipbox knows about panpsychism. "
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

        # Grade: output mentions existing panpsychism-related notes
        output = result["output"].lower()
        assert "panpsych" in output or "consciousness" in output or "faggin" in output, (
            "Exploration output should mention existing panpsychism notes"
        )

    def test_finds_similar_notes(self, seeded_slipbox, test_config):
        """LLM should find notes related to Faggin's quantum information panpsychism."""
        svc, refs = seeded_slipbox

        result = run_claude_eval(
            prompt=(
                "Find notes similar to my note about Faggin's quantum information "
                "panpsychism. What other notes in my slipbox are related?"
            ),
            notes_dir=svc.repository.notes_dir,
            db_path=test_config.get_absolute_path(test_config.database_path),
        )
        assert result["exit_code"] == 0, f"claude failed: {result['stderr']}"

        # Grade: output should mention at least one related note
        output = result["output"].lower()
        related_mentions = (
            "iit" in output
            or "integrated information" in output
            or "panpsychism overview" in output
            or "spinoza" in output
            or "irreducible" in output
            or "consciousness" in output
        )
        assert related_mentions, (
            f"Expected mention of related notes (IIT, Spinoza, panpsychism overview). "
            f"Output: {output[:500]}"
        )

    def test_identifies_knowledge_gaps(self, seeded_slipbox, test_config):
        """LLM should identify underrepresented areas in the slipbox."""
        svc, refs = seeded_slipbox

        result = run_claude_eval(
            prompt=(
                "What topics are underrepresented in my slipbox? "
                "Where are the gaps in my knowledge collection?"
            ),
            notes_dir=svc.repository.notes_dir,
            db_path=test_config.get_absolute_path(test_config.database_path),
        )
        assert result["exit_code"] == 0, f"claude failed: {result['stderr']}"

        # Grade: output should be substantive and mention areas with few connections
        output = result["output"].lower()
        # The output should mention at least some gap analysis -- fleeting notes,
        # cooking/pasta orphan, or areas with thin coverage
        has_analysis = (
            "fleeting" in output
            or "orphan" in output
            or "isolated" in output
            or "gap" in output
            or "underrepresented" in output
            or "pasta" in output
            or "cooking" in output
            or "russellian" in output
        )
        assert has_analysis, (
            f"Expected gap analysis in output. Output: {output[:500]}"
        )
