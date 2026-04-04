"""MCP resource registrations."""
from datetime import datetime


def register_resources(server) -> None:
    """Register all MCP resources on the given server."""
    mcp = server.mcp
    cluster_service = server.cluster_service

    @mcp.resource("slipbox://maintenance-status")
    def get_maintenance_status() -> dict:
        """Current Zettelkasten maintenance status.

        Returns pending cluster information for proactive maintenance prompts.
        Check this at session start to surface housekeeping opportunities.
        """
        report = cluster_service.load_report()

        if not report or not report.clusters:
            return {
                "pending_maintenance": False,
                "message": "No pending maintenance. Your Zettelkasten is well-organized!"
            }

        active_clusters = [
            c for c in report.clusters
            if c.id not in report.dismissed_cluster_ids
        ]

        if not active_clusters:
            return {
                "pending_maintenance": False,
                "message": "All detected clusters have been addressed or dismissed."
            }

        top = active_clusters[0]
        return {
            "pending_maintenance": True,
            "cluster_count": len(active_clusters),
            "top_cluster": {
                "id": top.id,
                "title": top.suggested_title,
                "note_count": top.note_count,
                "orphan_count": top.orphan_count,
                "tags": top.tags[:5],
                "score": top.score
            },
            "report_generated_at": report.generated_at.isoformat(),
            "report_age_hours": round(
                (datetime.now() - report.generated_at).total_seconds() / 3600, 1
            )
        }
