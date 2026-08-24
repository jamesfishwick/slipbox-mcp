"""Domain models and constants for cluster detection."""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, TypedDict

from pydantic import BaseModel, ConfigDict, Field

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


class ClusterCandidate(BaseModel):
    """A detected cluster that may need a structure note."""

    # Drop unknown keys so a report written by a newer version (with extra
    # fields) still loads rather than raising, matching the old tolerant load.
    model_config = ConfigDict(extra="ignore")

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


class ClusterReport(BaseModel):
    """Full cluster analysis report."""

    model_config = ConfigDict(extra="ignore")

    generated_at: datetime
    clusters: List[ClusterCandidate]
    stats: ClusterStats
    dismissed_cluster_ids: List[str] = Field(default_factory=list)
