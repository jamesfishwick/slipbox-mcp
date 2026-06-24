#!/usr/bin/env python3
"""Generate the slipbox skills from the MCP prompt templates.

Single source of truth: the PROMPT_* templates in
src/slipbox_mcp/server/descriptions.py — the same strings the MCP server
serves as prompts. This script wraps each one as a standalone Claude skill so
the two can't drift. Edit the template, re-run this; never hand-edit SKILL.md.

Outputs:
  skills/<name>/SKILL.md   browsable source + Claude Code skill discovery
  dist/<name>.skill        zip (<name>/SKILL.md) for Claude Desktop upload

Run:  python scripts/build_skills.py
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from slipbox_mcp.server.descriptions import (  # noqa: E402
    PROMPT_ANALYZE_NOTE,
    PROMPT_KNOWLEDGE_CREATION,
    PROMPT_KNOWLEDGE_CREATION_BATCH,
    PROMPT_KNOWLEDGE_EXPLORATION,
    PROMPT_KNOWLEDGE_SYNTHESIS,
)

GENERATED_NOTICE = (
    "<!-- Generated from src/slipbox_mcp/server/descriptions.py by "
    "scripts/build_skills.py. Do not edit by hand. -->"
)


def workflow_body(template: str) -> str:
    """Strip the trailing {content}/{topic} interpolation and its label.

    The prompt templates end with the user's pasted input; a skill takes that
    input from the conversation instead, so everything after (and the `---`
    separator / label introducing it) is dropped.
    """
    body = template
    for token in ("{content}", "{topic}"):
        body = body.split(token, 1)[0]
    body = body.rstrip()
    suffixes = ("---", "Note to analyze:", "Topic/concept to explore:")
    changed = True
    while changed:
        changed = False
        for suffix in suffixes:
            if body.endswith(suffix):
                body = body[: -len(suffix)].rstrip()
                changed = True
    return body


# Each skill: dir/command name, triggering description, and the body source.
# Template-derived skills share their workflow with the MCP prompt verbatim.
# cluster_maintenance's prompt is a runtime-rendered message, not a workflow,
# so its skill body is authored here (it drives the same cluster tools).
SKILLS = [
    {
        "name": "slipbox-knowledge-creation",
        "title": "Knowledge Creation",
        "description": (
            "Use when adding new information to the slipbox — articles, ideas, "
            "or notes to process into atomic Zettelkasten notes. Trigger on: add "
            "this to my slipbox, capture this, process this into notes, make notes "
            "from this. Grounds everything in the real slipbox via MCP tools."
        ),
        "body": workflow_body(PROMPT_KNOWLEDGE_CREATION),
    },
    {
        "name": "slipbox-knowledge-creation-batch",
        "title": "Knowledge Creation (Batch)",
        "description": (
            "Use when processing larger volumes into the slipbox — books, long "
            "articles, or collections needing 5-10 atomic notes. Trigger on: "
            "process this book, batch this chapter into notes, turn this long "
            "article into notes. Grounds everything in the real slipbox via MCP tools."
        ),
        "body": workflow_body(PROMPT_KNOWLEDGE_CREATION_BATCH),
    },
    {
        "name": "slipbox-knowledge-exploration",
        "title": "Knowledge Exploration",
        "description": (
            "Use when exploring how a topic connects to existing slipbox "
            "knowledge — discovering connections, finding hubs, identifying gaps, "
            "mapping the graph around a concept. Trigger on: how does X connect to "
            "my notes, what do I already know about X, map my thinking on X."
        ),
        "body": workflow_body(PROMPT_KNOWLEDGE_EXPLORATION),
    },
    {
        "name": "slipbox-knowledge-synthesis",
        "title": "Knowledge Synthesis",
        "description": (
            "Use when looking for higher-order insights across the slipbox — "
            "bridging unconnected areas, resolving contradictions, extending "
            "chains of thought, creating synthesis notes from emergent patterns. "
            "Trigger on: synthesize my notes on X, find bridges between Y and Z, "
            "what higher-order ideas connect these."
        ),
        "body": workflow_body(PROMPT_KNOWLEDGE_SYNTHESIS),
    },
    {
        "name": "slipbox-analyze-note",
        "title": "Analyze Note",
        "description": (
            "Analyze and improve a note for slipbox integration using the actual "
            "slipbox via MCP tools. Use when the user shares a note and asks to "
            "analyze it, improve it, integrate it, check atomicity, find "
            "connections, suggest tags, or refine it. Trigger on: analyze this "
            "note, check this zettel, is this atomic, what should this connect to, "
            "suggest tags for this note. Searches before suggesting connections."
        ),
        "body": workflow_body(PROMPT_ANALYZE_NOTE),
    },
    {
        "name": "slipbox-cluster-maintenance",
        "title": "Cluster Maintenance",
        "description": (
            "Use at the start of a slipbox session to surface pending housekeeping "
            "— knowledge clusters grown large enough to need a structure note. "
            "Trigger on: any slipbox maintenance, what needs attention in my "
            "slipbox, check my clusters, start-of-session housekeeping."
        ),
        "body": (
            "Surface pending Zettelkasten housekeeping, grounded in the actual "
            "slipbox.\n\n"
            "1. Load the current cluster analysis with `slipbox_get_cluster_report`. "
            "If it looks stale, run `slipbox_refresh_clusters` first.\n"
            "2. Report the top clusters that lack a structure note, ranked by "
            "urgency score (note count, orphan ratio, link density, recency).\n"
            "3. For each, show its suggested title, note/orphan counts, score, and "
            "ID.\n"
            "4. Offer to: create a structure note for one "
            "(`slipbox_create_structure_from_cluster`), show more detail, skip for "
            "now, or dismiss permanently (`slipbox_dismiss_cluster`).\n\n"
            "If no clusters need attention, say so — the slipbox is well-organized."
        ),
    },
]


def render(skill: dict) -> str:
    return (
        "---\n"
        f"name: {skill['name']}\n"
        f"description: \"{skill['description']}\"\n"
        "---\n\n"
        f"{GENERATED_NOTICE}\n\n"
        f"# {skill['title']}\n\n"
        f"{skill['body']}\n"
    )


def main() -> None:
    skills_dir = REPO / "skills"
    dist_dir = REPO / "dist"
    dist_dir.mkdir(exist_ok=True)

    for skill in SKILLS:
        name = skill["name"]
        content = render(skill)

        md_path = skills_dir / name / "SKILL.md"
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(content)

        bundle = dist_dir / f"{name}.skill"
        with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"{name}/SKILL.md", content)

        print(f"  {name}: skills/{name}/SKILL.md + dist/{name}.skill")

    print(f"Generated {len(SKILLS)} skills.")


if __name__ == "__main__":
    main()
