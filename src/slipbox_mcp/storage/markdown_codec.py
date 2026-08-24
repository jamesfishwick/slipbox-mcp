"""Pure markdown parse/serialize codec for notes.

This module owns the stateless conversion logic between the on-disk markdown
representation (frontmatter + ``## Links`` block), the database row
representation (``DBNote``), and the domain ``Note`` model. It holds no
repository, session, or filesystem state, so it can be reused anywhere a note
needs to be parsed or rendered without touching storage.
"""

import datetime
import logging
from typing import Any, List, Optional

import frontmatter
from pydantic import ValidationError

from slipbox_mcp.models.db_models import DBNote
from slipbox_mcp.models.schema import Link, LinkType, Note, NoteType, Tag
from slipbox_mcp.storage.note_id import is_safe_note_id

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Markdown parsing helpers (module-level, no instance state needed)
# ---------------------------------------------------------------------------


def _parse_frontmatter_tags(raw: Any) -> list[Tag]:
    """Parse tags from frontmatter value (str, list, or None)."""
    if isinstance(raw, str):
        tag_names = [t.strip() for t in raw.split(",") if t.strip()]
    elif isinstance(raw, list):
        tag_names = [str(t).strip() for t in raw if str(t).strip()]
    else:
        return []
    return [Tag(name=name) for name in tag_names]


def _parse_links_section(content: str, source_id: str) -> list[Link]:
    """Parse the ``## Links`` block from note content."""
    links: list[Link] = []
    in_links = False
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("## Links"):
            in_links = True
            continue
        if in_links and stripped.startswith("## "):
            in_links = False
            continue
        if in_links and stripped.startswith("- "):
            try:
                if "[[" in stripped and "]]" in stripped:
                    parts = stripped.split("[[", 1)
                    link_type_str = parts[0].strip()
                    if link_type_str.startswith("- "):
                        link_type_str = link_type_str[2:].strip()
                    id_and_desc = parts[1].split("]]", 1)
                    target_id = id_and_desc[0].strip()
                    description = None
                    if len(id_and_desc) > 1:
                        description = id_and_desc[1].strip()
                    try:
                        link_type = LinkType(link_type_str)
                    except ValueError:
                        link_type = LinkType.REFERENCE
                    links.append(
                        Link(
                            source_id=source_id,
                            target_id=target_id,
                            link_type=link_type,
                            description=description,
                            created_at=datetime.datetime.now(),
                        )
                    )
            except Exception as e:
                logger.error("Error parsing link: %s - %s", line, e)
    return links


def _coerce_frontmatter_datetime(value: Any) -> Optional[datetime.datetime]:
    """Coerce a frontmatter date value into a datetime.

    PyYAML auto-parses unquoted ISO-8601 timestamps into datetime objects,
    while quoted values arrive as strings. Accept both so a hand-edited or
    externally-generated note doesn't break indexing.
    """
    if isinstance(value, datetime.datetime):
        return value
    if isinstance(value, str) and value:
        return datetime.datetime.fromisoformat(value)
    return None


def _parse_frontmatter_dates(
    metadata: dict[str, Any],
) -> tuple[datetime.datetime, datetime.datetime]:
    """Parse created/updated datetimes from frontmatter metadata."""
    created_at = (
        _coerce_frontmatter_datetime(metadata.get("created")) or datetime.datetime.now()
    )
    updated_at = _coerce_frontmatter_datetime(metadata.get("updated")) or created_at
    return created_at, updated_at


class NoteMarkdownCodec:
    """Stateless codec for note (de)serialization.

    Converts between markdown text, ``DBNote`` rows, and domain ``Note``
    objects. Holds no state, so a single shared instance is safe.
    """

    def parse(self, content: str) -> Optional[Note]:
        """Parse a note from markdown content."""
        post = frontmatter.loads(content)
        metadata = post.metadata

        note_id = metadata.get("id")
        if not note_id:
            return None
        if not is_safe_note_id(note_id):
            # The id is not an accepted stem: either a path-traversal attempt
            # (``../../etc/x``, ``/etc/x``) or merely a legacy id using chars
            # outside [A-Za-z0-9_-] (e.g. a dot or space from before the id was
            # constrained). Skip it rather than let it reach the model_construct
            # fallback below, which would bypass the id validator and make a
            # traversal id writable. Skipping is loud and actionable so a benign
            # legacy note is not lost silently -- rename its id to re-index it.
            logger.warning(
                "Skipping note %s: id %r is not an accepted stem "
                "(allowed: [A-Za-z0-9_-], 1-255 chars). If this is a legacy "
                "note, rename its frontmatter id to re-index it.",
                metadata.get("title", "<untitled>"),
                note_id,
            )
            return None

        title = metadata.get("title")
        if not title:
            for line in post.content.strip().split("\n"):
                if line.startswith("# "):
                    title = line[2:].strip()
                    break
        if not title:
            raise ValueError("Note title missing from frontmatter or content")

        note_type_str = metadata.get("type", NoteType.PERMANENT.value)
        try:
            note_type = NoteType(note_type_str)
        except ValueError:
            note_type = NoteType.PERMANENT

        tags = _parse_frontmatter_tags(metadata.get("tags", ""))
        links = _parse_links_section(post.content, source_id=note_id)
        created_at, updated_at = _parse_frontmatter_dates(metadata)

        refs_raw = metadata.get("references", [])
        if isinstance(refs_raw, list):
            references = [str(r) for r in refs_raw if str(r).strip()]
        elif isinstance(refs_raw, str):
            references = [r.strip() for r in refs_raw.split("\n") if r.strip()]
        else:
            references = []

        kwargs = dict(
            id=note_id,
            title=title,
            content=post.content,
            note_type=note_type,
            tags=tags,
            links=links,
            references=references,
            created_at=created_at,
            updated_at=updated_at,
            metadata={
                k: v
                for k, v in metadata.items()
                if k
                not in [
                    "id",
                    "title",
                    "type",
                    "tags",
                    "created",
                    "updated",
                    "references",
                ]
            },
        )
        try:
            return Note(**kwargs)
        except ValidationError as e:
            # Existing on-disk note violates current schema (e.g. literature
            # without references after the new validator landed). Hydrate via
            # model_construct so the note remains visible to queries; surface
            # the violation via the audit-references CLI.
            logger.warning(
                "Schema violation hydrating note %s from markdown "
                "(run `slipbox audit-references`): %s",
                note_id,
                e.errors()[0].get("msg", str(e)),
            )
            return Note.model_construct(**kwargs)

    def db_note_to_note(self, db_note: DBNote) -> Note:
        """Convert a DBNote (with eager-loaded relationships) to a domain Note.

        Avoids per-note file I/O by using data already loaded from the database.
        Requires that db_note.tags, db_note.outgoing_links, and
        db_note.incoming_links have been eager-loaded in the calling query.
        """
        tags = [Tag(name=t.name) for t in db_note.tags]
        links = [
            Link(
                source_id=lnk.source_id,
                target_id=lnk.target_id,
                link_type=LinkType(lnk.link_type),
                description=lnk.description,
                created_at=lnk.created_at,
            )
            for lnk in db_note.outgoing_links
        ]
        kwargs: dict[str, Any] = dict(
            id=db_note.id,
            title=db_note.title,
            content=db_note.content,
            note_type=NoteType(db_note.note_type),
            tags=tags,
            links=links,
            references=db_note.references,
            created_at=db_note.created_at,
            updated_at=db_note.updated_at,
        )
        try:
            return Note(**kwargs)
        except ValidationError as e:
            # DB row violates current schema (e.g. literature without
            # references after the new validator landed). Hydrate via
            # model_construct so the note remains visible to queries; surface
            # the violation via the audit-references CLI.
            logger.warning(
                "Schema violation hydrating note %s from DB "
                "(run `slipbox audit-references`): %s",
                db_note.id,
                e.errors()[0].get("msg", str(e)),
            )
            return Note.model_construct(**kwargs)

    def convert_db_notes(self, db_notes: List[DBNote]) -> List[Note]:
        """Convert a list of DBNote objects to domain Notes, skipping conversion errors."""
        notes = []
        for db_note in db_notes:
            try:
                notes.append(self.db_note_to_note(db_note))
            except Exception as e:
                logger.error("Error converting note %s: %s", db_note.id, e)
        return notes

    def note_to_markdown(self, note: Note) -> str:
        """Convert a note to markdown with frontmatter."""
        metadata = {
            "id": note.id,
            "title": note.title,
            "type": note.note_type.value,
            "tags": [tag.name for tag in note.tags],
            "created": note.created_at.isoformat(),
            "updated": note.updated_at.isoformat(),
        }
        if note.references:
            metadata["references"] = note.references
        metadata.update(note.metadata)

        # Avoid duplicate title heading.
        title_heading = f"# {note.title}"
        if note.content.strip().startswith(title_heading):
            content = note.content
        else:
            content = f"{title_heading}\n\n{note.content}"

        # Strip existing Links section before rewriting.
        content_parts = []
        skip_section = False
        for line in content.split("\n"):
            if line.strip() == "## Links":
                skip_section = True
                continue
            elif skip_section and line.startswith("## "):
                skip_section = False

            if not skip_section:
                content_parts.append(line)

        content = "\n".join(content_parts).rstrip()

        # Deduplicates links by target+type key.
        if note.links:
            unique_links = {}
            for link in note.links:
                key = f"{link.target_id}:{link.link_type.value}"
                unique_links[key] = link
            content += "\n\n## Links\n"
            for link in unique_links.values():
                desc = f" {link.description}" if link.description else ""
                content += f"- {link.link_type.value} [[{link.target_id}]]{desc}\n"

        post = frontmatter.Post(content, **metadata)
        # frontmatter has no type stubs, so dumps() is typed Any; it returns str.
        return str(frontmatter.dumps(post))
