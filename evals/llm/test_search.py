"""LLM eval: search and discovery workflows.

Tests that Claude correctly uses MCP tools to find and surface information
from the slipbox. Requires claude CLI to be installed and authenticated.
"""
import pytest
from evals.conftest import run_claude_eval


@pytest.mark.eval
class TestSearch:

    def test_finds_notes_by_topic(self, seeded_slipbox, test_config):
        """LLM should find panpsychism-related notes when asked."""
        svc, refs = seeded_slipbox

        result = run_claude_eval(
            prompt=(
                "What notes do I have about panpsychism? "
                "List them with their titles."
            ),
            notes_dir=svc.repository.notes_dir,
            db_path=test_config.get_absolute_path(test_config.database_path),
        )
        assert result["exit_code"] == 0, f"claude failed: {result['stderr']}"

        # Grade: output should mention at least 2 of the panpsychism-related notes
        # (Faggin, IIT, Russellian Monism, Panpsychism Overview, Spinoza)
        output = result["output"].lower()
        mentions = sum([
            "faggin" in output or "quantum" in output,
            "iit" in output or "integrated information" in output,
            "panpsychism overview" in output or "russellian" in output,
        ])
        assert mentions >= 2, (
            f"Expected output to mention at least 2 panpsychism-related notes, "
            f"found {mentions}. Output: {output[:500]}"
        )

    def test_finds_connections_between_topics(self, seeded_slipbox, test_config):
        """LLM should identify connections between panpsychism and Wittgenstein."""
        svc, refs = seeded_slipbox

        result = run_claude_eval(
            prompt=(
                "How does panpsychism connect to Wittgenstein's philosophy in "
                "my slipbox? Trace the connections between these topics."
            ),
            notes_dir=svc.repository.notes_dir,
            db_path=test_config.get_absolute_path(test_config.database_path),
        )
        assert result["exit_code"] == 0, f"claude failed: {result['stderr']}"

        # Grade: output should mention the hard problem (bridge between branches)
        # and at least one note from each branch
        output = result["output"].lower()
        assert "hard problem" in output or "consciousness" in output or "qualia" in output, (
            f"Expected mention of hard problem / consciousness. Output: {output[:500]}"
        )
        panpsychism_mentions = (
            "faggin" in output
            or "panpsych" in output
            or "spinoza" in output
            or "iit" in output
        )
        assert panpsychism_mentions, (
            f"Expected mention of panpsychism-related note. Output: {output[:500]}"
        )

    def test_identifies_orphan_notes(self, seeded_slipbox, test_config):
        """LLM should find the unconnected pasta recipe note."""
        svc, refs = seeded_slipbox

        result = run_claude_eval(
            prompt=(
                "Are there any isolated notes in my slipbox that aren't "
                "connected to anything? Find orphan notes."
            ),
            notes_dir=svc.repository.notes_dir,
            db_path=test_config.get_absolute_path(test_config.database_path),
        )
        assert result["exit_code"] == 0, f"claude failed: {result['stderr']}"

        # Grade: output should mention the pasta recipe orphan
        output = result["output"].lower()
        assert "pasta" in output or "recipe" in output or "cooking" in output, (
            f"Expected mention of the pasta recipe orphan note. Output: {output[:500]}"
        )
