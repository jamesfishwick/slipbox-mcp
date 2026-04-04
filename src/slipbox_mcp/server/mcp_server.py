"""MCP server implementation for the Zettelkasten."""
import logging
import uuid
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from slipbox_mcp.config import config
from slipbox_mcp.services.search_service import SearchService
from slipbox_mcp.services.cluster_service import ClusterService
from slipbox_mcp.services.zettel_service import ZettelService

logger = logging.getLogger(__name__)


class ZettelkastenMcpServer:
    """MCP server for Zettelkasten."""
    def __init__(self):
        self.mcp = FastMCP(
            config.server_name
        )
        self.zettel_service = ZettelService()
        self.search_service = SearchService(self.zettel_service)
        self.cluster_service = ClusterService(self.zettel_service)
        self.initialize()
        self._register_tools()
        self._register_resources()
        self._register_prompts()

    def initialize(self) -> None:
        """Initialize services."""
        self._maybe_refresh_clusters()
        logger.info("Zettelkasten MCP server initialized")

    def _maybe_refresh_clusters(self) -> None:
        """Refresh cluster analysis if the report is stale (>24h old)."""
        try:
            report = self.cluster_service.load_report()

            should_refresh = False
            if not report:
                should_refresh = True
            else:
                age_hours = (datetime.now() - report.generated_at).total_seconds() / 3600
                should_refresh = age_hours > 24

            if should_refresh:
                logger.info("Refreshing stale cluster report...")
                new_report = self.cluster_service.detect_clusters()
                # Preserve dismissed clusters from old report
                if report:
                    new_report.dismissed_cluster_ids = report.dismissed_cluster_ids
                self.cluster_service.save_report(new_report)
                logger.info("Cluster report refreshed: %s", new_report.stats)
        except Exception as e:
            logger.warning("Failed to refresh clusters on startup: %s", e)

    def format_error_response(self, error: Exception) -> str:
        """Format an error response for MCP tool callers."""
        error_id = str(uuid.uuid4())[:8]

        if isinstance(error, ValueError):
            logger.error("Validation error [%s]: %s", error_id, error)
            return f"Error: {error}"
        elif isinstance(error, (IOError, OSError)):
            logger.error("File system error [%s]: %s", error_id, error, exc_info=True)
            return f"Error: {error}"
        else:
            logger.error("Unexpected error [%s]: %s", error_id, error, exc_info=True)
            return f"Error: {error}"

    def _register_tools(self) -> None:
        """Register MCP tools."""
        from slipbox_mcp.server.tools import register_all_tools
        register_all_tools(self)

    def _register_resources(self) -> None:
        from slipbox_mcp.server.resources import register_resources
        register_resources(self)

    def _register_prompts(self) -> None:
        """Register MCP prompts for knowledge workflows."""
        from slipbox_mcp.server.prompts import register_prompts
        register_prompts(self)

        @self.mcp.prompt()
        def analyze_note(content: str) -> str:
            """Analyze and improve a note for Zettelkasten integration.

            Use this workflow to evaluate a note's fitness for your slipbox.
            Checks atomicity, finds real connections using your existing notes,
            suggests tags from your taxonomy, and surfaces emergent insights.

            Args:
                content: The note content to analyze (or note ID for existing notes)
            """
            return f"""Analyze this note for integration into my Zettelkasten. Use the slipbox tools to ground your suggestions in my actual knowledge base.

## 1. Atomicity Check

Does the note contain exactly one idea? If multiple concepts are present:
- List each distinct idea that should be its own note
- Identify the primary idea vs. supporting details
- Search first to flag any that duplicate existing notes

## 2. Connectivity Analysis

**Do this before suggesting connections:**
1. Extract 2-3 key terms from the note
2. Run `zk_search_notes` for each term to find related existing notes
3. Run `zk_find_similar_notes` if this is an existing note ID
4. Check `zk_find_central_notes` to see if this relates to a knowledge hub

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

**Tags:** Run `zk_get_all_tags` first. Suggest 3-5 tags, preferring existing tags over new ones. If proposing a new tag, justify why existing tags don't fit.

**Title:** Propose a clear, searchable title that expresses the core idea.

**Note type:**
- `fleeting` — raw capture, needs processing
- `literature` — extracted from a source (requires citation)
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
[clean version ready for zk_create_note]

### Emergent Insights
[questions, gaps, unexpected connections]
```

---

Note to analyze:

{content}"""

    def run(self) -> None:
        """Run the MCP server."""
        self.mcp.run()
