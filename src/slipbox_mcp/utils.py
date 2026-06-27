"""Utility functions for the Zettelkasten MCP server."""

import logging
import os
import sys
import tempfile
from enum import Enum
from pathlib import Path
from typing import Optional, TypeVar

E = TypeVar("E", bound=Enum)


def atomic_write_text(path: Path, text: str) -> None:
    """Write *text* to *path* atomically via a temp file + os.replace.

    The replace is atomic on POSIX, so a crash mid-write leaves either the old
    file or the complete new one -- never a half-written file. The temp file is
    created in the target directory (same filesystem) so the rename can't fail
    with EXDEV, and is cleaned up if anything before the replace raises.
    """
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """Set up logging configuration."""
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO

    log_config = {
        "level": numeric_level,
        "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        "datefmt": "%Y-%m-%d %H:%M:%S",
    }

    if log_file:
        log_config["filename"] = log_file
        log_config["filemode"] = "a"
    else:
        log_config["stream"] = sys.stderr

    logging.basicConfig(**log_config)


def parse_tags(tags_str: Optional[str]) -> list[str]:
    """Parse a comma-separated list of tags into a list of tag strings."""
    if not tags_str:
        return []
    return [tag.strip() for tag in tags_str.split(",") if tag.strip()]


def parse_refs(references: Optional[str]) -> list[str]:
    """Parse a newline-separated references string into a list of stripped entries."""
    if not references:
        return []
    return [r.strip() for r in references.split("\n") if r.strip()]


def content_preview(text: str, max_length: int = 100) -> str:
    """Return a single-line preview of *text*, truncated with ellipsis if needed."""
    preview = text[:max_length].replace("\n", " ")
    if len(text) > max_length:
        preview += "..."
    return preview


def format_tags(tags: list) -> str:
    """Format a list of Tag objects as a comma-separated string."""
    return ", ".join(tag.name for tag in tags)


def parse_enum(
    value: str, enum_cls: type[E], label: str
) -> tuple[Optional[E], Optional[str]]:
    """Parse a string into an enum member (case-insensitive by value).

    Returns ``(member, None)`` on success and ``(None, error_message)`` on
    failure. The error message matches what the MCP tools have always returned
    for an invalid type, so tool output is unchanged.
    """
    try:
        return enum_cls(value.lower()), None
    except ValueError:
        valid = ", ".join(t.value for t in enum_cls)
        return None, f"Invalid {label}: {value}. Valid types are: {valid}"
