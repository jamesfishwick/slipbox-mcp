"""MCP prompt registrations for knowledge workflows."""


def register_prompts(server) -> None:
    """Register all MCP prompts on the given server."""
    mcp = server.mcp
    cluster_service = server.cluster_service

    @mcp.prompt()
    def cluster_maintenance() -> str:
        """Check for pending cluster maintenance and offer to help.

        Call this at the start of a session to proactively surface
        Zettelkasten housekeeping opportunities.
        """
        report = cluster_service.load_report()

        if not report or not report.clusters:
            return "No pending cluster maintenance. Your Zettelkasten is well-organized!"

        active_clusters = [
            c for c in report.clusters
            if c.id not in report.dismissed_cluster_ids
        ]

        if not active_clusters:
            return "All detected clusters have been addressed or dismissed."

        cluster_summaries = []
        for c in active_clusters[:3]:
            cluster_summaries.append(
                f"- **{c.suggested_title}** ({c.note_count} notes, {c.orphan_count} orphans, score: {c.score})\n"
                f"  Tags: {', '.join(c.tags[:4])}\n"
                f"  ID: `{c.id}`"
            )

        return f"""I found {len(active_clusters)} knowledge cluster(s) that might benefit from structure notes.

Top candidates:
{chr(10).join(cluster_summaries)}

Would you like me to:
1. **Create a structure note** for one of these clusters? (Just name it)
2. **Show more details** about a specific cluster?
3. **Skip for now** - I'll ask again next session
4. **Dismiss permanently** - Don't ask about these specific clusters again

Just let me know which cluster interests you, or say "skip" to move on."""

    @mcp.prompt()
    def knowledge_creation(content: str) -> str:
        """Process new information into atomic Zettelkasten notes.

        Use this workflow when you have text, articles, or ideas to add to your
        knowledge base. The workflow searches for existing related notes, extracts
        atomic ideas, creates properly linked notes, and updates structure notes.

        Args:
            content: The information to process (article text, notes, ideas, etc.)
        """
        return f"""I've attached information I'd like to incorporate into my Zettelkasten. Please:

First, search for existing notes that might be related before creating anything new.

Then, identify 3-5 key atomic ideas from this information and for each one:
1. Create a note with an appropriate title, type, and tags
2. Draft content in my own words with proper attribution
3. Find and create meaningful connections to existing notes
4. Update any relevant structure notes

After processing all ideas, provide a summary of the notes created, connections established, and any follow-up questions you have.

---

{content}"""

    @mcp.prompt()
    def knowledge_creation_batch(content: str) -> str:
        """Process larger volumes of information into the Zettelkasten.

        Use this workflow for processing books, long articles, or collections of
        related material. Extracts 5-10 atomic ideas, organizes them into clusters,
        and ensures quality and consistency with existing notes.

        Args:
            content: The larger text or collection to process
        """
        return f"""I've attached a larger text/collection of information to process into my Zettelkasten. Please:

1. First identify main themes and check my existing system for related notes and tags

2. Extract 5-10 distinct atomic ideas from this material, organized into logical clusters
   - Eliminate any concepts that duplicate my existing notes
   - Process each validated concept into a note with appropriate type, title, tags, and content
   - Create connections between related notes in this batch
   - Connect each new note to relevant existing notes in my system

3. Update or create structure notes as needed to integrate this batch of knowledge

4. Verify quality for each note:
   - Each note contains a single focused concept
   - All sources are properly cited
   - Each note has meaningful connections
   - Terminology is consistent with my existing system

Provide a summary of all notes created, connections established, and structure notes updated, along with any areas you've identified for follow-up work.

---

{content}"""

    @mcp.prompt()
    def knowledge_exploration(topic: str) -> str:
        """Explore how a topic connects to existing knowledge.

        Use this workflow to discover connections, find knowledge hubs, identify
        gaps, and map how new information relates to your existing Zettelkasten.

        Args:
            topic: The topic or concept to explore
        """
        return f"""I'd like to explore how this information connects to my existing Zettelkasten. Please:

1. Identify the central concepts in this information and find related notes in my system

2. Examine knowledge hubs in my Zettelkasten by:
   - Finding central notes related to these concepts
   - Mapping their connections and similar notes
   - Identifying promising knowledge paths to follow

3. Look for any gaps, contradictions, or orphaned notes that relate to these concepts

4. Create a conceptual map showing:
   - How this information fits with my existing knowledge
   - Unexpected connections discovered
   - Potential areas for development

Finally, summarize what you've learned about my Zettelkasten through this exploration and highlight the most valuable insights found.

---

Topic/concept to explore: {topic}"""

    @mcp.prompt()
    def knowledge_synthesis(content: str) -> str:
        """Synthesize higher-order insights from connected knowledge.

        Use this workflow to find bridges between unconnected areas, resolve
        contradictions, extend chains of thought, and create new permanent notes
        capturing emergent insights.

        Args:
            content: Information or context that might spark synthesis opportunities
        """
        return f"""I've attached information that might help synthesize ideas in my Zettelkasten. Please:

1. Find opportunities for synthesis by identifying:
   - Potential bridges between currently unconnected areas in my system
   - Contradictions that this information might help resolve
   - Incomplete chains of thought that could now be extended

2. For the most promising synthesis opportunities (3-5 max):
   - Create new permanent notes capturing the higher-order insights
   - Connect these synthesis notes to the contributing notes with appropriate link types
   - Update or create structure notes as needed

3. Identify any relevant fleeting notes that should be converted to permanent notes in light of this synthesis

4. Based on this synthesis work, highlight:
   - New questions that have emerged
   - Knowledge gaps revealed
   - Potential applications of the new understanding

Provide a summary of the insights discovered, notes created, and connections established through this synthesis process.

---

{content}"""
