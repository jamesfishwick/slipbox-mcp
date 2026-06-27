"""Service for searching and discovering notes in the Zettelkasten."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Set, Tuple, Union

from sqlalchemy import select, text
from sqlalchemy.exc import OperationalError

from slipbox_mcp.models.db_models import DBNote, DBTag
from slipbox_mcp.models.schema import Note, NoteType
from slipbox_mcp.services.zettel_service import ZettelService
from slipbox_mcp.storage.note_repository import _NOTE_EAGER_LOADS

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

    def __init__(self, zettel_service: Optional[ZettelService] = None):
        self.zettel_service = zettel_service or ZettelService()

    def _run_fts5_query(self, fts_query: str) -> list:
        """Execute an FTS5 MATCH query and return raw result rows.

        Returns list of rows with (id, bm25_score, matched_context).
        Returns [] on FTS5 syntax errors. Re-raises on missing tables.
        """
        repository = self.zettel_service.repository
        sql = text("""
            SELECT
                n.id,
                bm25(notes_fts) AS bm25_score,
                snippet(notes_fts, 1, '', '', '...', 8) AS matched_context
            FROM notes_fts
            JOIN notes n ON notes_fts.rowid = n.rowid
            WHERE notes_fts MATCH :query
            ORDER BY bm25(notes_fts)
        """)
        with repository.session_factory() as session:
            try:
                return session.execute(sql, {"query": fts_query}).fetchall()
            except OperationalError as e:
                err = str(e).lower()
                if "no such table" in err:
                    if "notes_fts" in err:
                        logger.error(
                            "FTS5 table 'notes_fts' missing -- run slipbox_rebuild_index: %s",
                            e,
                        )
                    else:
                        logger.error(
                            "Required table missing from database schema: %s", e
                        )
                    raise
                if "fts5" in err or (
                    "unterminated string" in err and "notes_fts" in err
                ):
                    logger.warning("FTS5 query syntax error for %r: %s", fts_query, e)
                    return []
                raise

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

        results = []
        for row in rows:
            note = repository.get(row.id)
            if note is None:
                continue
            # bm25() returns negative float; negate so higher = better
            score = -row.bm25_score
            results.append(
                SearchResult(
                    note=note,
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
        date_col = DBNote.updated_at if use_updated else DBNote.created_at
        repository = self.zettel_service.repository

        with repository.session_factory() as session:
            query = select(DBNote).options(*_NOTE_EAGER_LOADS)
            if start_date:
                query = query.where(date_col >= start_date)
            if end_date:
                query = query.where(date_col <= end_date)
            query = query.order_by(date_col.desc())

            result = session.execute(query)
            db_notes = result.unique().scalars().all()
            return [repository._db_note_to_note(db_note) for db_note in db_notes]

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

        with repository.session_factory() as session:
            query = select(DBNote).options(*_NOTE_EAGER_LOADS)
            if note_type:
                query = query.where(DBNote.note_type == note_type.value)
            if start_date:
                query = query.where(DBNote.created_at >= start_date)
            if end_date:
                query = query.where(DBNote.created_at <= end_date)
            if tags:
                query = query.where(DBNote.tags.any(DBTag.name.in_(tags)))

            db_notes = session.execute(query).unique().scalars().all()
            candidate_ids = {db_note.id: db_note for db_note in db_notes}

            # Treat a missing or whitespace-only query_text as "no text filter":
            # return the metadata-matched candidates rather than running an empty
            # MATCH (which would swallow a misleading FTS5 syntax error to []).
            if not query_text or not query_text.strip():
                notes = [repository._db_note_to_note(n) for n in db_notes]
                return [
                    SearchResult(
                        note=n, score=1.0, matched_terms=set(), matched_context=""
                    )
                    for n in notes
                ]

            fts_query = _build_fts_match(query_text)

        fts_rows = self._run_fts5_query(fts_query)

        results = []
        for row in fts_rows:
            if row.id not in candidate_ids:
                continue
            note = repository._db_note_to_note(candidate_ids[row.id])
            score = -row.bm25_score
            results.append(
                SearchResult(
                    note=note,
                    score=score,
                    matched_terms=set(query_text.split()),
                    matched_context=f"Content: ...{row.matched_context}...",
                )
            )

        return results
