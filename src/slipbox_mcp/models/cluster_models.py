"""Domain models and constants for cluster detection."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, TypedDict

MIN_CLUSTER_SIZE = 5
CO_OCCURRENCE_THRESHOLD = 3
REPORT_PATH = Path("~/.local/share/mcp/slipbox/cluster-analysis.json").expanduser()


class ClusterStats(TypedDict):
    """Aggregate counts attached to a cluster report.

    A TypedDict (not a model) because every producer, consumer, and the JSON
    round-trip treat it as a plain dict; this just pins the keys and value
    types for static checking.
    """

    total_notes: int
    total_orphans: int
    clusters_detected: int
    clusters_needing_structure: int


@dataclass
class ClusterCandidate:
    """A detected cluster that may need a structure note."""

    id: str
    suggested_title: str
    tags: List[str]
    notes: List[Dict[str, str]]  # [{id, title}, ...]
    note_count: int
    orphan_count: int
    internal_links: int
    density: float
    score: float
    newest_date: Optional[datetime] = None


@dataclass
class ClusterReport:
    """Full cluster analysis report."""

    generated_at: datetime
    clusters: List[ClusterCandidate]
    stats: ClusterStats
    dismissed_cluster_ids: List[str] = field(default_factory=list)
