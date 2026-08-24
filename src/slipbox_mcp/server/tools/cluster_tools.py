"""Cluster analysis and structure note tools."""

import logging
from typing import TYPE_CHECKING, Optional

from slipbox_mcp.formatting import format_cluster_summary
from slipbox_mcp.models.cluster_models import ClusterReport
from slipbox_mcp.server.descriptions import (
    SLIPBOX_CREATE_STRUCTURE_FROM_CLUSTER,
    SLIPBOX_DISMISS_CLUSTER,
    SLIPBOX_GET_CLUSTER_REPORT,
    SLIPBOX_REFRESH_CLUSTERS,
)
from slipbox_mcp.server.tools import tool_error_handler

if TYPE_CHECKING:
    from slipbox_mcp.server.mcp_server import ZettelkastenMcpServer

logger = logging.getLogger(__name__)


def register_cluster_tools(server: "ZettelkastenMcpServer") -> None:
    """Register cluster-related MCP tools."""
    mcp = server.mcp
    cluster_service = server.cluster_service
    handle = tool_error_handler(server.format_error_response)

    @mcp.tool(name="slipbox_get_cluster_report", description=SLIPBOX_GET_CLUSTER_REPORT)
    @handle
    def slipbox_get_cluster_report(
        min_score: float = 0.5,
        limit: int = 5,
        include_notes: bool = False,
        refresh: bool = False,
    ) -> str:
        if not 0.0 <= min_score <= 1.0:
            logger.warning(
                "slipbox_get_cluster_report: min_score %r out of range [0.0, 1.0]",
                min_score,
            )
            return "Error: min_score must be between 0.0 and 1.0."
        if limit <= 0:
            logger.warning(
                "slipbox_get_cluster_report: limit %r must be a positive integer",
                limit,
            )
            return "Error: limit must be a positive integer."
        report: ClusterReport
        if refresh:
            report = cluster_service.detect_clusters()
            cluster_service.save_report(report)
        else:
            loaded = cluster_service.load_report()
            if loaded is None:
                report = cluster_service.detect_clusters()
                cluster_service.save_report(report)
            else:
                report = loaded

        clusters = [c for c in report.clusters if c.score >= min_score][:limit]

        if not clusters:
            return f"No clusters found with score >= {min_score}. Try lowering min_score or running with refresh=True."

        output = f"Cluster Analysis (generated {report.generated_at.strftime('%Y-%m-%d %H:%M')})\n"
        output += f"Stats: {report.stats['total_notes']} notes, {report.stats['total_orphans']} orphans, "
        output += f"{report.stats['clusters_needing_structure']} clusters need structure notes\n\n"

        for i, cluster in enumerate(clusters, 1):
            output += format_cluster_summary(
                cluster, index=i, include_notes=include_notes
            )

        return output

    @mcp.tool(
        name="slipbox_create_structure_from_cluster",
        description=SLIPBOX_CREATE_STRUCTURE_FROM_CLUSTER,
    )
    @handle
    def slipbox_create_structure_from_cluster(
        cluster_id: str, title: Optional[str] = None, create_links: bool = True
    ) -> str:
        report = cluster_service.load_report()
        if not report:
            return "No cluster report found. Run slipbox_get_cluster_report(refresh=True) first."

        cluster = next((c for c in report.clusters if c.id == cluster_id), None)
        if not cluster:
            available = ", ".join(c.id for c in report.clusters[:5])
            return f"Cluster '{cluster_id}' not found. Available: {available}"

        structure_note, links_created = cluster_service.create_structure_note(
            cluster, title, create_links
        )

        return (
            f"Structure note created: {structure_note.title} "
            f"(ID: {structure_note.id})\n"
            f"Linked to {links_created}/{len(cluster.notes)} member notes."
        )

    @mcp.tool(name="slipbox_refresh_clusters", description=SLIPBOX_REFRESH_CLUSTERS)
    @handle
    def slipbox_refresh_clusters() -> str:
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

    @mcp.tool(name="slipbox_dismiss_cluster", description=SLIPBOX_DISMISS_CLUSTER)
    @handle
    def slipbox_dismiss_cluster(cluster_id: str) -> str:
        report = cluster_service.load_report()
        if not report:
            return "No cluster report found. Run slipbox_refresh_clusters first."

        if cluster_id not in [c.id for c in report.clusters]:
            available = ", ".join(c.id for c in report.clusters[:5])
            return f"Cluster '{cluster_id}' not found. Available clusters: {available}"

        cluster_service.dismiss_cluster(cluster_id)
        return (
            f"Cluster '{cluster_id}' dismissed. You won't be reminded about it again."
        )
