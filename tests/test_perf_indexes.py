"""The foreign-key indexes SQLite does not create automatically must exist.

SQLite auto-creates an index for UNIQUE constraints but not for foreign keys,
so incoming-link traversal, orphan detection, centrality, deletes, and reverse
tag joins would full-scan without these. Assert they are emitted into the schema.
"""

from sqlalchemy import create_engine, inspect

from slipbox_mcp.models.db_models import Base


def test_link_and_tag_indexes_exist_in_schema():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    insp = inspect(engine)

    link_indexes = {ix["name"] for ix in insp.get_indexes("links")}
    assert "ix_links_target_id" in link_indexes
    assert "ix_links_source_id" in link_indexes

    note_tags_indexes = {ix["name"] for ix in insp.get_indexes("note_tags")}
    assert "ix_note_tags_tag_id" in note_tags_indexes
