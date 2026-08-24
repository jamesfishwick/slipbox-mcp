"""Path-safe note-id validation, shared by the repository and the codec.

Note IDs become filenames (``{id}.md``), so they are constrained to a path-safe
alphabet: a crafted id (``../../etc/x``, ``/etc/x``) cannot escape the notes dir.
This mirrors the validator on ``Note.id`` exactly -- same alphabet AND the same
1..255 length bound -- and is applied at the filesystem layer so ids that
bypassed model validation (e.g. ``Note.model_construct`` on the schema-violation
hydration path) are still refused.

This is a dependency-free leaf module so both ``note_repository`` and
``markdown_codec`` can import it at module load without a circular import.
"""

import re
from typing import Any

_NOTE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,255}$")


def is_safe_note_id(note_id: Any) -> bool:
    """Return True if note_id is a non-empty, path-safe filename stem."""
    return isinstance(note_id, str) and bool(_NOTE_ID_PATTERN.fullmatch(note_id))
