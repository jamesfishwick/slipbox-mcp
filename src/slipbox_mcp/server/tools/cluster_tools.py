"""Cluster analysis and structure note tools."""
import logging
from typing import Optional
from slipbox_mcp.models.schema import LinkType, NoteType

logger = logging.getLogger(__name__)


def register_cluster_tools(server) -> None:
    """Register cluster-related MCP tools."""
    mcp = server.mcp
    cluster_service = server.cluster_service
    zettel_service = server.zettel_service
    format_error = server.format_error_response

    @mcp.tool(name="zk_get_cluster_report")
    def zk_get_cluster_report(
        min_score: float = 0.5,
        limit: int = 5,
        include_notes: bool = False,
        refresh: bool = False
    ) -> str:
        """Get pending cluster analysis for structure note creation.

        Clusters are groups of notes sharing tags but lacking a structure note.
        High-scoring clusters are good candidates for new structure notes.

        Uses cached analysis by default. Set refresh=true to regenerate.
        Cluster analysis runs automatically via cron if configured.

        Scoring factors:
        - Note count (7-15 is ideal, >15 is overdue)
        - Orphan ratio (more orphans = more urgent)
        - Internal link density (fewer links = needs structure)
        - Recency (recent activity = active domain)

        Args:
            min_score: Minimum cluster score 0.0-1.0 (default: 0.5)
            limit: Maximum clusters to return (default: 5)
            include_notes: Include full note list per cluster (default: false)
            refresh: Force regeneration of cluster analysis (default: false)
        """
        try:
            if not 0.0 <= min_score <= 1.0:
                logger.warning("zk_get_cluster_report: min_score %r out of range [0.0, 1.0]", min_score)
                return "Error: min_score must be between 0.0 and 1.0."
            if limit <= 0:
                logger.warning("zk_get_cluster_report: limit %r must be a positive integer", limit)
                return "Error: limit must be a positive integer."
            if refresh:
                report = cluster_service.detect_clusters()
                cluster_service.save_report(report)
            else:
                report = cluster_service.load_report()
                if not report:
                    report = cluster_service.detect_clusters()
                    cluster_service.save_report(report)

            clusters = [c for c in report.clusters if c.score >= min_score][:limit]

            if not clusters:
                return f"No clusters found with score >= {min_score}. Try lowering min_score or running with refresh=True."

            output = f"Cluster Analysis (generated {report.generated_at.strftime('%Y-%m-%d %H:%M')})\n"
            output += f"Stats: {report.stats['total_notes']} notes, {report.stats['total_orphans']} orphans, "
            output += f"{report.stats['clusters_needing_structure']} clusters need structure notes\n\n"

            for i, cluster in enumerate(clusters, 1):
                output += f"{i}. {cluster.suggested_title}\n"
                output += f"   ID: {cluster.id}\n"
                output += f"   Score: {cluster.score} | Notes: {cluster.note_count} | Orphans: {cluster.orphan_count}\n"
                output += f"   Tags: {', '.join(cluster.tags)}\n"

                if include_notes:
                    output += "   Notes:\n"
                    for note in cluster.notes[:10]:
                        output += f"     - {note['title']} ({note['id']})\n"
                    if len(cluster.notes) > 10:
                        output += f"     ... and {len(cluster.notes) - 10} more\n"
                output += "\n"

            return output
        except Exception as e:
            return format_error(e)

    @mcp.tool(name="zk_create_structure_from_cluster")
    def zk_create_structure_from_cluster(
        cluster_id: str,
        title: Optional[str] = None,
        create_links: bool = True
    ) -> str:
        """Create a structure note from a detected cluster.

        Generates a structure note organizing all notes in the cluster,
        with bidirectional links to each member note.

        Run zk_get_cluster_report first to see available clusters and their IDs.

        Args:
            cluster_id: ID from cluster report (e.g. "jackson-mac-low-chance-operations")
            title: Override the suggested title (optional)
            create_links: Create bidirectional links to member notes (default: true)
        """
        try:
            report = cluster_service.load_report()
            if not report:
                return "No cluster report found. Run zk_get_cluster_report(refresh=True) first."

            cluster = next((c for c in report.clusters if c.id == cluster_id), None)
            if not cluster:
                available = ', '.join(c.id for c in report.clusters[:5])
                return f"Cluster '{cluster_id}' not found. Available: {available}"

            final_title = title or cluster.suggested_title
            content = f"Structure note for {len(cluster.notes)} related notes.\n\n"
            content += f"## Overview\n\nThis cluster emerged from notes sharing these tags: {', '.join(cluster.tags)}.\n\n"
            content += "## Member Notes\n\n"

            for note_info in cluster.notes:
                content += f"- [[{note_info['id']}]] {note_info['title']}\n"

            content += "\n## Synthesis\n\n_TODO: Synthesize key insights from these notes._\n"

            structure_note = zettel_service.create_note(
                title=final_title,
                content=content,
                note_type=NoteType.STRUCTURE,
                tags=cluster.tags[:5]
            )

            links_created = 0
            if create_links:
                for note_info in cluster.notes:
                    try:
                        zettel_service.create_link(
                            source_id=structure_note.id,
                            target_id=note_info['id'],
                            link_type=LinkType.REFERENCE,
                            description="Member of structure note",
                            bidirectional=True
                        )
                        links_created += 1
                    except Exception as link_error:
                        logger.warning("Failed to create link to %s: %s", note_info['id'], link_error)

            cluster_service.dismiss_cluster(cluster_id)

            return f"Structure note created: {final_title} (ID: {structure_note.id})\nLinked to {links_created}/{len(cluster.notes)} member notes."
        except Exception as e:
            return format_error(e)

    @mcp.tool(name="zk_refresh_clusters")
    def zk_refresh_clusters() -> str:
        """Regenerate cluster analysis and save report.

        Analyzes all notes for emergent clusters based on:
        - Tag co-occurrence (tags that frequently appear together)
        - Connection patterns (notes that link to each other)
        - Structure note coverage (which clusters already have structure notes)

        Results saved to ~/.local/share/mcp/slipbox/cluster-analysis.json
        """
        try:
            report = cluster_service.detect_clusters()
            path = cluster_service.save_report(report)

            output = "Cluster analysis complete.\n"
            output += f"Report saved to: {path}\n\n"
            output += "Stats:\n"
            output += f"  Total notes: {report.stats['total_notes']}\n"
            output += f"  Orphaned notes: {report.stats['total_orphans']}\n"
            output += f"  Clusters detected: {report.stats['clusters_detected']}\n"
            output += f"  Clusters needing structure: {report.stats['clusters_needing_structure']}\n"

            if report.clusters:
                output += "\nTop clusters:\n"
                for cluster in report.clusters[:3]:
                    output += f"  - {cluster.suggested_title} (score: {cluster.score})\n"

            return output
        except Exception as e:
            return format_error(e)

    @mcp.tool(name="zk_dismiss_cluster")
    def zk_dismiss_cluster(cluster_id: str) -> str:
        """Permanently dismiss a cluster from maintenance suggestions.

        Use this when a cluster has been reviewed and determined not to need
        a structure note, or when the user doesn't want to be reminded about it.

        Args:
            cluster_id: The cluster ID to dismiss (e.g. "poetry-craft-revision")
        """
        try:
            report = cluster_service.load_report()
            if not report:
                return "No cluster report found. Run zk_refresh_clusters first."

            if cluster_id not in [c.id for c in report.clusters]:
                available = ', '.join(c.id for c in report.clusters[:5])
                return f"Cluster '{cluster_id}' not found. Available clusters: {available}"

            cluster_service.dismiss_cluster(cluster_id)
            return f"Cluster '{cluster_id}' dismissed. You won't be reminded about it again."
        except Exception as e:
            return format_error(e)
