"""Configuration module for the Zettelkasten MCP server."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

from slipbox_mcp import __version__

load_dotenv()


def _expand_path(raw: str) -> Path:
    """Expand ~ in path strings and raise if expansion fails (e.g. ~nonexistentuser)."""
    expanded = os.path.expanduser(raw)
    if expanded.startswith("~"):
        raise ValueError(
            f"Path {raw!r} could not be expanded to an absolute path. "
            "Use a full absolute path instead of a tilde shortcut."
        )
    return Path(expanded)


def ensure_private_dir(path: Path) -> Path:
    """Create ``path`` (and parents) as an owner-only (0o700) directory.

    Notes and the SQLite index can contain private material, so data
    directories must not be world-readable under a permissive umask. ``mode``
    on ``mkdir`` only applies to newly created dirs and is itself masked by the
    process umask, so a pre-existing (or umask-narrowed) dir is re-tightened
    with an explicit ``chmod``. On platforms without POSIX permissions the
    ``chmod`` is a best-effort no-op and any failure is ignored.

    Returns the path for convenient chaining.
    """
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        os.chmod(path, 0o700)
    except OSError:
        # Best effort: some filesystems/platforms don't support POSIX modes.
        pass
    return path


class ZettelkastenConfig(BaseModel):
    """Configuration for the Zettelkasten server.

    The ``SLIPBOX_*`` path environment variables (``SLIPBOX_BASE_DIR``,
    ``SLIPBOX_NOTES_DIR``, ``SLIPBOX_DATABASE_PATH``) are used as-is and are
    not sandboxed. Point them at a **dedicated data directory** you control,
    not at a shared or system location: the server creates and manages the
    notes tree and the SQLite index under these paths (with owner-only
    permissions), and ``rebuild_index`` treats the notes directory as the
    source of truth.
    """

    base_dir: Path = Field(
        default_factory=lambda: _expand_path(os.getenv("SLIPBOX_BASE_DIR", "."))
    )
    notes_dir: Path = Field(
        default_factory=lambda: _expand_path(
            os.getenv("SLIPBOX_NOTES_DIR", "data/notes")
        )
    )
    database_path: Path = Field(
        default_factory=lambda: _expand_path(
            os.getenv("SLIPBOX_DATABASE_PATH", "data/db/zettelkasten.db")
        )
    )
    server_name: str = Field(default=os.getenv("SLIPBOX_SERVER_NAME", "slipbox-mcp"))
    server_version: str = Field(default=__version__)
    id_date_format: str = Field(default="%Y%m%dT%H%M%S")

    def get_absolute_path(self, path: Path) -> Path:
        """Convert a relative path to an absolute path based on base_dir."""
        if path.is_absolute():
            return path
        return self.base_dir / path

    def get_db_url(self) -> str:
        """Get the database URL for SQLite."""
        db_path = self.get_absolute_path(self.database_path)
        ensure_private_dir(db_path.parent)
        return f"sqlite:///{db_path}"


try:
    config = ZettelkastenConfig()
except (ValueError, ValidationError) as e:
    print(f"Configuration error: {e}", file=sys.stderr)
    raise SystemExit(1) from e
