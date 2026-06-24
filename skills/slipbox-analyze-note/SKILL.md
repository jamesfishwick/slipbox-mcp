---
name: slipbox-analyze-note
description: "Analyze and improve a note for slipbox integration using the actual slipbox via MCP tools. Use when the user shares a note and asks to analyze it, improve it, integrate it, check atomicity, find connections, suggest tags, or refine it. Trigger on: analyze this note, check this zettel, is this atomic, what should this connect to, suggest tags for this note. Searches before suggesting connections."
---

<!-- Generated from src/slipbox_mcp/server/descriptions.py by scripts/build_skills.py. Do not edit by hand. -->

# Analyze Note

Analyze this note for integration into my Zettelkasten. Use the slipbox tools to ground your suggestions in my actual knowledge base.

## 1. Atomicity Check

Does the note contain exactly one idea? If multiple concepts are present:
- List each distinct idea that should be its own note
- Identify the primary idea vs. supporting details
- Search first to flag any that duplicate existing notes

## 2. Connectivity Analysis

**Do this before suggesting connections:**
1. Extract 2-3 key terms from the note
2. Run `slipbox_search_notes` for each term to find related existing notes
3. Run `slipbox_find_similar_notes` if this is an existing note ID
4. Check `slipbox_find_central_notes` to see if this relates to a knowledge hub

**Then report:**
- Specific existing notes this should link to (with IDs and titles)
- Recommended link types for each connection:
  - `extends` — builds on the target note
  - `refines` — clarifies or improves the target
  - `contradicts` — presents opposing view
  - `questions` — raises doubts about the target
  - `supports` — provides evidence for the target
  - `related` — loose thematic connection

## 3. Clarity Enhancement

Rewrite the note to:
- Express one idea clearly and completely
- Stand alone without external context
- Use terminology consistent with existing notes (check related notes for conventions)
- Stay within 3-7 paragraphs

Provide the rewritten version in a code block for easy copying.

## 4. Metadata Suggestions

**Tags:** Run `slipbox_get_all_tags` first. Suggest 3-5 tags, preferring existing tags over new ones. If proposing a new tag, justify why existing tags don't fit.

**Title:** Propose a clear, searchable title that expresses the core idea.

**Note type:**
- `fleeting` — raw capture, needs processing
- `literature` — extracted from a source. REQUIRES at least one entry in `references`. Use `fleeting` if you don't have the citation yet.
- `permanent` — refined idea in user's own words
- `structure` — organizes 7-15 related notes on a topic
- `hub` — entry point to a major knowledge domain

## 5. Emergent Insights

Based on what you found in the slipbox:
- Questions this note raises that aren't answered by existing notes
- Gaps in the knowledge graph this could help fill
- Unexpected connections to distant topics in the slipbox
- Potential cluster this belongs to (check if related notes share tags but lack a structure note)

---

## Output Format

```
### Atomicity: [PASS | SPLIT NEEDED]
[analysis]

### Connections Found
| Existing Note | Link Type | Reason |
|---------------|-----------|--------|
| [title] (ID)  | extends   | ...    |

### Suggested Tags
[from existing taxonomy, or justified new tags]

### Proposed Title
[title]

### Note Type
[type with rationale]

### Rewritten Note
[clean version ready for slipbox_create_note]

### Emergent Insights
[questions, gaps, unexpected connections]
```
