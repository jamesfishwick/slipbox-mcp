"""MCP server implementation for the Zettelkasten."""

import logging
import uuid
from datetime import datetime

from mcp.server.fastmcp import FastMCP
from pydantic import ValidationError

from slipbox_mcp.config import config
from slipbox_mcp.server.descriptions import SERVER_INSTRUCTIONS
from slipbox_mcp.services import build_services

logger = logging.getLogger(__name__)


class ZettelkastenMcpServer:
    """MCP server for Zettelkasten."""

    def __init__(self) -> None:
        self.mcp = FastMCP(config.server_name, instructions=SERVER_INSTRUCTIONS)
        services = build_services()
        self.zettel_service = services.zettel
        self.search_service = services.search
        self.cluster_service = services.cluster
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
                age_hours = (
                    datetime.now() - report.generated_at
                ).total_seconds() / 3600
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

        # A duplicate link trips the (source_id, target_id, link_type) UNIQUE
        # constraint. Translate it to a caller-friendly message here, once, so
        # every tool that can create a link benefits rather than each catching
        # it itself. Match on the message text alone (not the exception type),
        # preserving the pre-refactor breadth: a UNIQUE violation surfaced as any
        # exception, not only a SQLAlchemy IntegrityError, still gets this. The
        # "links." scope keeps it from mislabeling a future table's UNIQUE
        # constraint as a duplicate link.
        error_text = str(error)
        if "UNIQUE constraint failed" in error_text and "links." in error_text:
            logger.info("Duplicate link rejected [%s]: %s", error_id, error)
            return (
                "A link of this type already exists between these notes. "
                "Try a different link type."
            )

        # ValidationError must be checked before ValueError: in Pydantic v2 it
        # subclasses ValueError, so a generic str(error) would surface the full
        # multi-line dump and bury the validator's curated message.
        if isinstance(error, ValidationError):
            logger.error("Validation error [%s]: %s", error_id, error)
            errors = error.errors()
            if errors:
                return f"Error: {errors[0]['msg']}"
            return f"Error: {error}"
        elif isinstance(error, ValueError):
            # ValueError messages are curated validator text, not raw paths, so
            # they are safe to surface to the caller.
            logger.error("Validation error [%s]: %s", error_id, error)
            return f"Error: {error}"
        elif isinstance(error, (IOError, OSError)):
            # Filesystem errors carry absolute paths in their message; return a
            # generic response plus a correlation id and log the full detail so
            # operators can look it up without leaking paths to the caller.
            logger.error("File system error [%s]: %s", error_id, error, exc_info=True)
            return (
                f"Error: a file system error occurred while handling the request. "
                f"Reference this error id when reporting the issue: {error_id}"
            )
        else:
            # Unexpected errors may embed internal detail (paths, stack context);
            # keep the same generic-message + correlation-id contract.
            logger.error("Unexpected error [%s]: %s", error_id, error, exc_info=True)
            return (
                f"Error: an unexpected error occurred while handling the request. "
                f"Reference this error id when reporting the issue: {error_id}"
            )

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

    def run(self) -> None:
        """Run the MCP server."""
        self.mcp.run()
