"""The foreign-key indexes SQLite does not create automatically must exist.

SQLite auto-creates an index for UNIQUE constraints but not for foreign keys,
so incoming-link traversal, orphan detection, centrality, deletes, and reverse
tag joins would full-scan without these. Assert they are emitted into the schema
on fresh databases AND backfilled onto databases that predate them.
"""

from sqlalchemy import create_engine, inspect, text

from slipbox_mcp.models import db_models
from slipbox_mcp.models.db_models import Base


def _indexed_columns(inspector, table):
    return {ix["name"]: ix["column_names"] for ix in inspector.get_indexes(table)}


def test_link_and_tag_indexes_created_on_fresh_schema():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    insp = inspect(engine)

    links = _indexed_columns(insp, "links")
    assert links.get("ix_links_target_id") == ["target_id"]
    assert links.get("ix_links_source_id") == ["source_id"]

    note_tags = _indexed_columns(insp, "note_tags")
    assert note_tags.get("ix_note_tags_tag_id") == ["tag_id"]


def test_init_db_backfills_indexes_on_existing_database(tmp_path, monkeypatch):
    """init_db must add the FK indexes to a database that predates them:
    create_all skips existing tables, so the indexes need an explicit backfill.
    """
    db_path = tmp_path / "legacy.db"
    url = f"sqlite:///{db_path}"

    # Simulate a pre-index database: full schema, then drop the three indexes.
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    with engine.connect() as conn:
        for name in (
            "ix_links_target_id",
            "ix_links_source_id",
            "ix_note_tags_tag_id",
        ):
            conn.execute(text(f"DROP INDEX IF EXISTS {name}"))
        conn.commit()
    engine.dispose()

    # Run the real migration path against that database (point config at it via
    # the database_path field, as the test_config fixture does).
    monkeypatch.setattr(db_models.config, "database_path", db_path)
    migrated = db_models.init_db()

    insp = inspect(migrated)
    link_idx = {ix["name"] for ix in insp.get_indexes("links")}
    note_tags_idx = {ix["name"] for ix in insp.get_indexes("note_tags")}
    assert {"ix_links_target_id", "ix_links_source_id"} <= link_idx
    assert "ix_note_tags_tag_id" in note_tags_idx
