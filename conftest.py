"""Root conftest -- shared fixtures available to both tests/ and evals/."""
# Path shim: force this tree's src/ to the front of sys.path BEFORE any
# slipbox_mcp import resolves. The repo is installed editable in a shared
# .venv whose .pth points at the MAIN checkout, so a worktree's pytest run
# would otherwise import main's source while collecting the worktree's tests
# -- silently testing the wrong code. Prepending the local src/ overrides
# that. No-op when src/ isn't beside this file.
import sys as _sys
from pathlib import Path as _Path

_local_src = _Path(__file__).resolve().parent / "src"
if _local_src.is_dir():
    _src_str = str(_local_src)
    if _sys.path and _sys.path[0] == _src_str:
        pass
    else:
        # Drop any existing occurrence, then pin to front.
        _sys.path = [p for p in _sys.path if p != _src_str]
        _sys.path.insert(0, _src_str)

import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine

from slipbox_mcp.config import config
from slipbox_mcp.models.db_models import Base
from slipbox_mcp.services.zettel_service import ZettelService
from slipbox_mcp.storage.note_repository import NoteRepository


# ---------------------------------------------------------------------------
# Directory / config isolation
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_dirs():
    """Create temporary directories for notes and database."""
    with tempfile.TemporaryDirectory() as notes_dir:
        with tempfile.TemporaryDirectory() as db_dir:
            yield Path(notes_dir), Path(db_dir)


@pytest.fixture
def test_config(temp_dirs):
    """Configure with test paths, restoring originals after the test."""
    notes_dir, db_dir = temp_dirs
    database_path = db_dir / "test_zettelkasten.db"
    original_notes_dir = config.notes_dir
    original_database_path = config.database_path
    config.notes_dir = notes_dir
    config.database_path = database_path
    yield config
    config.notes_dir = original_notes_dir
    config.database_path = original_database_path


# ---------------------------------------------------------------------------
# Repository / service fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def note_repository(test_config):
    """Create an isolated NoteRepository backed by a fresh SQLite database."""
    database_path = test_config.get_absolute_path(test_config.database_path)
    engine = create_engine(f"sqlite:///{database_path}")
    Base.metadata.create_all(engine)
    engine.dispose()
    repository = NoteRepository(notes_dir=test_config.notes_dir)
    yield repository


@pytest.fixture
def zettel_service(note_repository):
    """Create a ZettelService wired to the isolated test repository."""
    service = ZettelService(repository=note_repository)
    yield service
