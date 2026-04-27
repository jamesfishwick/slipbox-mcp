# Roadmap

Where slipbox-mcp is headed. This is a living document -- priorities shift based on community feedback and real usage patterns.

## Near Term

### Multi-vault support

Currently the server binds to a single `SLIPBOX_BASE_DIR`. Supporting multiple vaults would let you keep separate knowledge bases (work, personal, research) that can optionally cross-reference each other.

### Improved similarity scoring

The current `slipbox_find_similar_notes` uses shared tags, common links, and content overlap. Adding embedding-based semantic similarity (via a local model or API) would catch conceptual connections that keyword overlap misses.

### Cross-cluster bridge detection

The current cluster tools measure how densely a cluster is linked *internally* and surface orphans, but don't scan between clusters for missing edges. The real drought in most slipboxes is at cluster boundaries -- notes articulating the same structural claim in different vocabularies (e.g. `editorial curation` in a poetry cluster and `context curation` in an AI-coding cluster) stay disconnected because they share no tags.

A `slipbox_find_missing_bridges` operation would, for each pair of tag clusters, return candidate note pairs with no existing link, no short path in the link graph, and content-overlap above a threshold -- ranked by strength. A companion workflow prompt lets the agent run the scan during cluster maintenance, suggest a link type, and submit candidates for user approval -- matching the propose-then-confirm shape of cluster-based structure notes.

### Note templates

Predefined templates for common note types (literature review, meeting notes, project retrospective) that the agent can use when creating notes, with consistent frontmatter and section structure.

### Export and visualization

- Export the knowledge graph as a standalone HTML visualization
- Generate Mermaid diagrams of local graph neighborhoods
- Produce summary reports of knowledge growth over time

## Medium Term

### Spaced repetition integration

Surface notes that haven't been reviewed recently. The Zettelkasten method works best when you revisit notes -- the system could suggest daily review candidates based on link density, age, and centrality.

### Collaborative knowledge bases

Multiple users contributing to the same vault, with attribution tracking. Requires conflict resolution for concurrent note edits and link creation.

### Plugin system for custom link types

The seven built-in link types cover most cases, but domain-specific workflows (academic research, legal analysis, medical knowledge) may need custom relationship types with their own traversal semantics.

## Long Term

### Cross-vault knowledge synthesis

Bridging insights across separate vaults without merging them. A "meta-graph" layer that can surface connections between your work knowledge base and your personal reading notes.

### Autonomous knowledge maintenance

Background agents that continuously monitor knowledge base health: detect stale notes, suggest link repairs after refactors, flag contradictions between notes, and propose cluster merges when topic areas converge.

---

Have an idea? Open an issue or start a discussion on [GitHub](https://github.com/jamesfishwick/slipbox-mcp).
