"""Service for searching and discovering notes in the Zettelkasten."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Set, Tuple, Union

from slipbox_mcp.models.schema import Note, NoteType
from slipbox_mcp.services.zettel_service import ZettelService

logger = logging.getLogger(__name__)


def _build_fts_match(query: str, column: Optional[str] = None) -> str:
    """Build an FTS5 MATCH expression from a free-text query.

    Each whitespace-separated token is wrapped in double quotes (so any FTS5
    special characters inside a token are treated as literal text) and the
    tokens are combined with OR. OR maximizes recall -- a note matches if it
    contains *any* term -- while BM25 ranking still floats notes that match
    more terms to the top.

    Wrapping the whole query in quotes instead would produce a single FTS5
    phrase query, which only matches when the tokens appear contiguously and
    in order. That is why multi-word searches previously returned nothing.

    ``column`` optionally scopes each term to a single FTS5 column
    (e.g. ``title`` or ``content``). Phrase search is intentionally
    unsupported -- every token is matched independently.
    """
    tokens = query.split()
    if not tokens:
        return ""
    prefix = f"{column}:" if column else ""
    quoted = []
    for tok in tokens:
        # Inside an FTS5 double-quoted string the only character needing
        # escaping is the double quote itself, escaped by doubling it.
        escaped = tok.replace('"', '""')
        quoted.append(f'{prefix}"{escaped}"')
    return " OR ".join(quoted)


@dataclass
class SearchResult:
    """A search result with a note and its relevance score."""

    note: Note
    score: float
    matched_terms: Set[str]
    matched_context: str


class SearchService:
    """Service for searching notes in the Zettelkasten."""

    def __init__(self, zettel_service: ZettelService):
        self.zettel_service = zettel_service

    @staticmethod
    def _build_result(
        note: Note,
        score: float = 1.0,
        matched_terms: Optional[Set[str]] = None,
        matched_context: str = "",
    ) -> SearchResult:
        """Construct a SearchResult with consistent defaults."""
        return SearchResult(
            note=note,
            score=score,
            matched_terms=matched_terms or set(),
            matched_context=matched_context,
        )

    def _run_fts5_query(self, fts_query: str) -> list:
        """Execute an FTS5 MATCH query and return raw result rows.

        Thin wrapper over the repository, kept as a seam so tests can patch
        it. Returns list of rows with (id, bm25_score, matched_context).
        Returns [] on FTS5 syntax errors. Re-raises on missing tables.
        """
        return self.zettel_service.repository.run_fts_match(fts_query)

    def search_by_text(
        self, query: str, include_content: bool = True, include_title: bool = True
    ) -> List[SearchResult]:
        """Search for notes by text using SQLite FTS5 with BM25 ranking."""
        if not query:
            return []

        repository = self.zettel_service.repository

        if include_title and include_content:
            fts_query = _build_fts_match(query)
        elif include_title:
            fts_query = _build_fts_match(query, column="title")
        else:
            fts_query = _build_fts_match(query, column="content")

        # A whitespace-only query yields no tokens; return [] explicitly rather
        # than letting an empty MATCH expression fall through to the FTS5
        # syntax-error catch (which would log a misleading "syntax error").
        if not fts_query:
            return []

        rows = self._run_fts5_query(fts_query)
        if not rows:
            return []

        # Hydrate every hit with a single batched DB query instead of one file
        # read per hit -- the same batching pattern find_central_notes and
        # search_combined use. The FTS index is DB-derived (an external-content
        # table kept in lockstep with notes by triggers), so DB content is
        # authoritative for what matched. Unlike the old repository.get() path
        # this never reads the backing file, so a corrupt-on-disk note with an
        # intact DB row is returned from the index rather than raising IOError.
        # On-disk corruption is surfaced by audit tooling, not by search.
        ordered_ids = [row.id for row in rows]
        db_notes_by_id = repository.get_notes_by_ids(ordered_ids)

        results = []
        for row in rows:
            note = db_notes_by_id.get(row.id)
            if note is None:
                # db_note is None only via a cross-transaction race: the FTS read
                # above (a separate transaction) matched the note, but it was
                # deleted before this batched hydrate query ran. notes_fts is an
                # external-content index kept in lockstep with notes by triggers,
                # so this is a TOCTOU gap between the two reads, not index-vs-table
                # drift. Skip it, mirroring the defensive skip in find_central_notes.
                logger.warning(
                    "search_by_text: note '%s' matched the FTS index but was gone "
                    "from the notes table at hydrate time (deleted between the FTS "
                    "read and this query); skipping",
                    row.id,
                )
                continue
            # bm25() returns negative float; negate so higher = better
            score = -row.bm25_score
            results.append(
                self._build_result(
                    note,
                    score=score,
                    matched_terms=set(query.split()),
                    matched_context=f"Content: ...{row.matched_context}...",
                )
            )

        return results

    def search_by_tag(self, tags: Union[str, List[str]]) -> List[Note]:
        """Search for notes by tags."""
        if isinstance(tags, str):
            return self.zettel_service.get_notes_by_tag(tags)
        return self.zettel_service.repository.search(tags=tags)

    def search_by_link(self, note_id: str, direction: str = "both") -> List[Note]:
        """Search for notes linked to/from a note."""
        return self.zettel_service.get_linked_notes(note_id, direction)

    def find_orphaned_notes(self) -> List[Note]:
        """Find notes with no incoming or outgoing links."""
        return self.zettel_service.repository.find_orphaned_notes()

    def find_central_notes(self, limit: int = 10) -> List[Tuple[Note, int]]:
        """Find notes with the most connections (incoming + outgoing links)."""
        return self.zettel_service.repository.find_central_notes(limit)

    def find_notes_by_date_range(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        use_updated: bool = False,
    ) -> List[Note]:
        """Find notes created or updated within a date range."""
        return self.zettel_service.repository.find_by_date_range(
            start_date=start_date,
            end_date=end_date,
            use_updated=use_updated,
        )

    def find_similar_notes(self, note_id: str) -> List[Tuple[Note, float]]:
        """Find notes similar to the given note based on shared tags and links."""
        return self.zettel_service.find_similar_notes(note_id)

    def search_combined(
        self,
        query_text: Optional[str] = None,
        tags: Optional[List[str]] = None,
        note_type: Optional[NoteType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[SearchResult]:
        """Perform a combined search: SQL pre-filter by metadata, FTS5 for text ranking."""
        repository = self.zettel_service.repository

        candidate_ids = repository.find_metadata_candidates(
            note_type=note_type,
            tags=tags,
            start_date=start_date,
            end_date=end_date,
        )

        # Treat a missing or whitespace-only query_text as "no text filter":
        # return the metadata-matched candidates rather than running an empty
        # MATCH (which would swallow a misleading FTS5 syntax error to []).
        if not query_text or not query_text.strip():
            return [self._build_result(n) for n in candidate_ids.values()]

        fts_query = _build_fts_match(query_text)

        fts_rows = self._run_fts5_query(fts_query)

        results = []
        for row in fts_rows:
            if row.id not in candidate_ids:
                continue
            note = candidate_ids[row.id]
            score = -row.bm25_score
            results.append(
                self._build_result(
                    note,
                    score=score,
                    matched_terms=set(query_text.split()),
                    matched_context=f"Content: ...{row.matched_context}...",
                )
            )

        return results
