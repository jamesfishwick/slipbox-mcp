"""Service layer for the Zettelkasten MCP server."""

from typing import NamedTuple, Optional

from slipbox_mcp.models.cluster_models import (  # noqa: F401
    ClusterCandidate as ClusterCandidate,
)
from slipbox_mcp.models.cluster_models import (
    ClusterReport as ClusterReport,
)
from slipbox_mcp.services.cluster_service import (  # noqa: F401
    ClusterService as ClusterService,
)
from slipbox_mcp.services.search_service import SearchService
from slipbox_mcp.services.zettel_service import ZettelService
from slipbox_mcp.storage.note_repository import NoteRepository


class Services(NamedTuple):
    """Wired service graph produced by :func:`build_services`."""

    repository: NoteRepository
    zettel: ZettelService
    search: SearchService
    cluster: ClusterService


def build_services(repository: Optional[NoteRepository] = None) -> Services:
    """Construct the service dependency graph.

    This is the single place that supplies a default ``NoteRepository`` and
    wires the services together. Every service otherwise requires its
    dependencies explicitly.
    """
    repo = repository or NoteRepository()
    zettel = ZettelService(repo)
    search = SearchService(zettel)
    cluster = ClusterService(zettel)
    return Services(repository=repo, zettel=zettel, search=search, cluster=cluster)
