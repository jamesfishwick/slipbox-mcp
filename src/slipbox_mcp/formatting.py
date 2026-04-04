"""Shared formatting helpers for MCP tools and CLI output."""
from __future__ import annotations

from slipbox_mcp.models.schema import Note


def content_preview(content: str, max_len: int = 150) -> str:
    """Truncate content to max_len, replacing newlines with spaces."""
    preview = content[:max_len].replace("\n", " ")
    if len(content) > max_len:
        preview += "..."
    return preview


def format_tag_list(tags) -> str:
    """Format tags as comma-separated string. Accepts Note.tags or plain strings."""
    if not tags:
        return ""
    names = [t.name if hasattr(t, "name") else str(t) for t in tags]
    return ", ".join(names)


def format_note_summary(
    note: Note,
    index: int = 0,
    preview_len: int = 150,
    extra_lines: list[str] | None = None,
) -> str:
    """Format a note as a numbered summary line with tags and preview.

    Args:
        note: The note to format.
        index: 1-based index for numbered lists (0 = no number prefix).
        preview_len: Max characters for content preview.
        extra_lines: Additional indented lines (e.g. "Similarity: 0.85").
    """
    prefix = f"{index}. " if index else ""
    lines = [f"{prefix}{note.title} (ID: {note.id})"]
    if extra_lines:
        for line in extra_lines:
            lines.append(f"   {line}")
    if note.tags:
        lines.append(f"   Tags: {format_tag_list(note.tags)}")
    lines.append(f"   Preview: {content_preview(note.content, preview_len)}")
    lines.append("")  # trailing blank line
    return "\n".join(lines) + "\n"


def format_note_compact(note: Note) -> str:
    """Format a note as a compact single line for CLI output.

    Format: "{id[:12]}  {title}"
    With optional tag line: "            [{tag1, tag2, tag3}]"
    """
    lines = [f"{note.id[:12]}  {note.title}"]
    if note.tags:
        tag_str = format_tag_list(note.tags[:3])
        lines.append(f"            [{tag_str}]")
    return "\n".join(lines)


def format_note_detail(note: Note) -> str:
    """Format a note with full metadata for display."""
    lines = [
        f"# {note.title}",
        f"ID: {note.id}",
        f"Type: {note.note_type.value}",
        f"Created: {note.created_at.isoformat()}",
        f"Updated: {note.updated_at.isoformat()}",
    ]
    if note.tags:
        lines.append(f"Tags: {format_tag_list(note.tags)}")
    if note.references:
        lines.append("References:")
        for ref in note.references:
            lines.append(f"  - {ref}")
    lines.append(f"\n{note.content}")
    return "\n".join(lines) + "\n"


def format_cluster_summary(
    cluster,
    index: int = 0,
    include_notes: bool = False,
) -> str:
    """Format a cluster as a summary block. Uses duck typing on cluster attributes."""
    prefix = f"{index}. " if index else ""
    lines = [
        f"{prefix}{cluster.suggested_title}",
        f"   ID: {cluster.id}",
        f"   Score: {cluster.score} | Notes: {cluster.note_count} | Orphans: {cluster.orphan_count}",
        f"   Tags: {format_tag_list(cluster.tags)}",
    ]
    if include_notes:
        lines.append("   Notes:")
        for note_info in cluster.notes[:10]:
            lines.append(f"     - {note_info['title']} ({note_info['id']})")
        if len(cluster.notes) > 10:
            lines.append(f"     ... and {len(cluster.notes) - 10} more")
    lines.append("")  # trailing blank line
    return "\n".join(lines) + "\n"
