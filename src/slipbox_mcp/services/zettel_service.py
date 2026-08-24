"""Service layer for Zettelkasten operations."""

import datetime
import logging
from typing import Any, Dict, List, Optional, Tuple

from slipbox_mcp.models.schema import LinkType, Note, NoteType, Tag
from slipbox_mcp.services.exceptions import NoteNotFoundError
from slipbox_mcp.storage.note_repository import NoteRepository

logger = logging.getLogger(__name__)


class ZettelService:
    """Service for managing Zettelkasten notes."""

    def __init__(self, repository: NoteRepository):
        self.repository = repository

    def _get_or_raise(self, note_id: str, label: str = "Note") -> Note:
        """Fetch a note by ID or raise NoteNotFoundError if it does not exist."""
        note = self.repository.get(note_id)
        if not note:
            raise NoteNotFoundError(note_id, label)
        return note

    def create_note(
        self,
        title: str,
        content: str,
        note_type: NoteType = NoteType.PERMANENT,
        tags: Optional[List[str]] = None,
        references: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Note:
        """Create a new note."""
        if not title:
            raise ValueError("Title is required")
        if not content:
            raise ValueError("Content is required")

        note = Note(
            title=title,
            content=content,
            note_type=note_type,
            tags=[Tag(name=tag) for tag in (tags or [])],
            references=references or [],
            metadata=metadata or {},
        )

        return self.repository.create(note)

    def get_note(self, note_id: str) -> Optional[Note]:
        """Retrieve a note by ID."""
        return self.repository.get(note_id)

    def get_note_by_title(self, title: str) -> Optional[Note]:
        """Retrieve a note by title."""
        return self.repository.get_by_title(title)

    def update_note(
        self,
        note_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        note_type: Optional[NoteType] = None,
        tags: Optional[List[str]] = None,
        references: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Note:
        """Update an existing note.

        Validates the merged target state atomically: builds a candidate dict
        from current state plus changes, then runs Note's full validator chain
        once. Avoids the partial-mutation hazard of per-attribute assignment
        with validate_assignment=True, where mid-update validation failure
        would leave the in-memory note partially modified.
        """
        note = self._get_or_raise(note_id)

        changes: Dict[str, Any] = {}
        if title is not None:
            changes["title"] = title
        if content is not None:
            changes["content"] = content
        if note_type is not None:
            changes["note_type"] = note_type
        if tags is not None:
            changes["tags"] = [Tag(name=tag) for tag in tags]
        if references is not None:
            changes["references"] = references
        if metadata is not None:
            changes["metadata"] = metadata
        changes["updated_at"] = datetime.datetime.now()

        merged = note.model_dump()
        merged.update(changes)
        validated = Note.model_validate(merged)

        return self.repository.update(validated)

    def delete_note(self, note_id: str) -> None:
        """Delete a note."""
        self.repository.delete(note_id)

    def get_all_notes(self) -> List[Note]:
        """Get all notes."""
        return self.repository.get_all()

    def get_notes_by_tag(self, tag: str) -> List[Note]:
        """Get notes by tag."""
        return self.repository.find_by_tag(tag)

    def add_tag_to_note(self, note_id: str, tag: str) -> Note:
        """Add a tag to a note."""
        note = self._get_or_raise(note_id)
        note.add_tag(tag)
        return self.repository.update(note)

    def remove_tag_from_note(self, note_id: str, tag: str) -> Note:
        """Remove a tag from a note."""
        note = self._get_or_raise(note_id)
        note.remove_tag(tag)
        return self.repository.update(note)

    def get_all_tags(self) -> List[Tag]:
        """Get all tags in the system."""
        return self.repository.get_all_tags()

    @staticmethod
    def _note_has_link(note: Note, target_id: str, link_type: LinkType) -> bool:
        """Return True if note already has a link of the given type to target_id."""
        return any(
            lnk.target_id == target_id and lnk.link_type == link_type
            for lnk in note.links
        )

    def create_link(
        self,
        source_id: str,
        target_id: str,
        link_type: LinkType = LinkType.REFERENCE,
        description: Optional[str] = None,
        bidirectional: bool = False,
        bidirectional_type: Optional[LinkType] = None,
    ) -> Tuple[Note, Optional[Note]]:
        """Create a link between notes with proper bidirectional semantics.

        Args:
            source_id: ID of the source note
            target_id: ID of the target note
            link_type: Type of link from source to target
            description: Optional description of the link
            bidirectional: Whether to create a link in both directions
            bidirectional_type: Optional custom link type for the reverse direction
                If not provided, an appropriate inverse relation will be used

        Returns:
            Tuple of (source_note, target_note or None)
        """
        source_note = self._get_or_raise(source_id, "Source note")
        target_note = self._get_or_raise(target_id, "Target note")

        if self._note_has_link(source_note, target_id, link_type):
            if not bidirectional:
                return source_note, None
        else:
            source_note.add_link(target_id, link_type, description)
            source_note = self.repository.update(source_note)

        # Add reverse link.
        reverse_note = None
        if bidirectional:
            if bidirectional_type is None:
                bidirectional_type = link_type.inverse

            if not self._note_has_link(target_note, source_id, bidirectional_type):
                target_note.add_link(source_id, bidirectional_type, description)
                reverse_note = self.repository.update(target_note)
            else:
                reverse_note = target_note

        return source_note, reverse_note

    def remove_link(
        self,
        source_id: str,
        target_id: str,
        link_type: Optional[LinkType] = None,
        bidirectional: bool = False,
    ) -> Tuple[Note, Optional[Note]]:
        """Remove a link between notes."""
        source_note = self._get_or_raise(source_id, "Source note")

        source_note.remove_link(target_id, link_type)
        source_note = self.repository.update(source_note)

        reverse_note = None
        if bidirectional:
            target_note = self.repository.get(target_id)
            if target_note:
                target_note.remove_link(source_id, link_type)
                reverse_note = self.repository.update(target_note)

        return source_note, reverse_note

    def get_linked_notes(self, note_id: str, direction: str = "outgoing") -> List[Note]:
        """Get notes linked to/from a note."""
        self._get_or_raise(note_id)  # validate existence; links come from the repo
        return self.repository.find_linked_notes(note_id, direction)

    def rebuild_index(self) -> None:
        """Rebuild the database index from files."""
        self.repository.rebuild_index()

    def export_note(self, note_id: str, format: str = "markdown") -> str:
        """Export a note in the specified format."""
        note = self._get_or_raise(note_id)

        if format.lower() == "markdown":
            try:
                return self.repository.note_to_markdown(note)
            except Exception as e:
                raise ValueError(
                    f"Failed to serialize note {note_id} to markdown: {e}"
                ) from e
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def find_similar_notes(
        self, note_id: str, threshold: float = 0.5
    ) -> List[Tuple[Note, float]]:
        """Find notes similar to the given note based on shared tags and links."""
        note = self._get_or_raise(note_id)

        results = []

        note_tags = note.tag_names()
        note_links = {link.target_id for link in note.links}

        incoming_notes = self.repository.find_linked_notes(note_id, "incoming")
        note_incoming = {n.id for n in incoming_notes}

        # A note that shares no tag or link with this one always scores 0, so
        # restrict scoring to candidates that share something instead of loading
        # the whole corpus. At threshold 0 the caller wants every note ranked
        # (0-similarity notes included), so fall back to the full set there.
        if threshold <= 0.0:
            candidates = self.repository.get_all()
        else:
            candidates = self.repository.find_similarity_candidates(note_id)

        for other_note in candidates:
            if other_note.id == note_id:
                continue

            other_tags = other_note.tag_names()
            tag_overlap = len(note_tags.intersection(other_tags))

            other_links = {link.target_id for link in other_note.links}
            link_overlap = len(note_links.intersection(other_links))

            incoming_overlap = 1 if other_note.id in note_incoming else 0
            outgoing_overlap = 1 if other_note.id in note_links else 0

            # Weight: 40% tags, 20% outgoing links, 20% incoming links, 20% direct connections
            total_possible = (
                max(len(note_tags), len(other_tags)) * 0.4
                + max(len(note_links), len(other_links)) * 0.2
                + 1 * 0.2
                + 1 * 0.2
            )

            if total_possible == 0:
                similarity = 0.0
            else:
                similarity = (
                    (tag_overlap * 0.4)
                    + (link_overlap * 0.2)
                    + (incoming_overlap * 0.2)
                    + (outgoing_overlap * 0.2)
                ) / total_possible

            if similarity >= threshold:
                results.append((other_note, similarity))

        results.sort(key=lambda x: x[1], reverse=True)
        return results
